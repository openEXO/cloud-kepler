# -*- coding: utf-8 -*-

import sys
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import scipy.optimize as opt
from sklearn.cluster import DBSCAN
from utils import setup_logging

# Basic logging configuration.
logger = setup_logging(__file__)


class NoClustersError(Exception):
    pass


class NonIntegerClustersError(Exception):
    pass


def clean_signal(time, flux, dtime, dflux, dfluxerr, out):
    # We restrict the "standard deviation" of the cluster to be 5% of the
    # size of the space.
    size = max(np.nanmax(np.absolute(out['depth_dip'])), np.nanmax(out['depth_blip']))
    mean_flux_err = 0.05 * size

    # Construct an array of all the useful quantities. We will only be finding
    # clusters in the first two dimensions! The other dimensions are for bookkeeping.
    ndx = np.where((out['srsq_dip'] > 0.) & (out['srsq_blip'] > 0.))
    X = np.column_stack((out['depth_dip'][ndx], out['depth_blip'][ndx],
        out['duration_dip'][ndx], out['duration_blip'][ndx], out['midtime_dip'][ndx],
        out['midtime_blip'][ndx]))

    metric = lambda x, y: np.sqrt((x[0] - y[0])**2. / mean_flux_err**2. +
        (x[1] - y[1])**2. / mean_flux_err**2.)

    db = DBSCAN(eps=1., min_samples=10, metric=metric).fit(X[:,0:2])
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_
    unique_labels = set(labels)

    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    if n_clusters_ < 2:
        logger.info('DBSCAN did not resolve two clusters in the '
            'depth_dip/depth_blip space; stopping algorithm')
        raise RuntimeError

    mean_depths = []

    for k in unique_labels:
        if k == -1:
            continue

        class_member_mask = (labels == k)
        mean_depths.append([np.mean(X[class_member_mask & core_samples_mask][:,0]),k])

    mean_depths = np.array(mean_depths)
    ndx = np.argmin(mean_depths[:,0])
    depth = mean_depths[ndx,0]
    k = int(mean_depths[ndx,1])

    # Construct a mask for members of this cluster.
    class_member_mask = (labels == k)

    try:
        best_period, best_duration, best_phase = __do_period_search(X, time,
            class_member_mask & core_samples_mask, err_flux=mean_flux_err)
    except NoClustersError:
        # We didn't find any clusters at all. This is a good place to stop.
        raise RuntimeError
    except NonIntegerClustersError:
        # Something weird is going on. Try one more time with a step of 2,
        # then quit, marking this system for further consideration.
        try:
            best_period, best_duration, best_phase = __do_period_search(X, time,
                class_member_mask & core_samples_mask, err_flux=mean_flux_err, step=2)
        except (NoClustersError, NonIntegerClustersError):
            logger.warning('DBSCAN found multiple clusters that do not look like '
                'integer multiples; investigate!')
            raise RuntimeError

    def boxcar(time, duration, depth, P, phase):
        pftime = np.mod(time, P)

        flux = np.zeros_like(time)
        ndx = np.where((pftime > phase - 0.5 * duration) &
            (pftime < phase + 0.5 * duration))
        flux[ndx] = depth

        return flux

    p0 = np.array([best_duration, depth, best_period, best_phase], dtype='float64')
    logger.info('Best guess boxcar parameters:\n\t' + str(p0))
    #logger.info(str(p0))

    #pftime = np.mod(dtime, p0[2])
    #ndx = np.where(np.isfinite(dflux))
    #plt.scatter(pftime, dflux)
    #plt.plot(pftime[ndx], boxcar(pftime[ndx], *p0), color='green')
    #plt.show()

    ndx = np.where(np.isfinite(dflux))
    f = lambda x: dflux[ndx] - boxcar(dtime[ndx], *x)
    pbest = opt.leastsq(f, p0)[0]
    logger.info('Best fit boxcar parameters:\n\t' + str(pbest))

    best_duration = pbest[0]
    best_period = pbest[2]
    best_phase = pbest[3]

    pftime = np.mod(time, best_period)
    ndx = np.where((pftime > best_phase - 2. * best_duration) &
        (pftime < best_phase + 2. * best_duration))
    flux[ndx] = np.nan


def __do_period_search(X, time, mask, step=1, err_midtime=0.1, err_flux=0.01,
max_period_err=0.1):
    # Remove all samples not in the core of this cluster from the data array.
    # The bookkeeping parameters are still around at this point.
    Y = X[mask][::step]
    Y[0:-1,1] = np.diff(Y[:,4])
    Y = Y[0:-1,:]

    metric = lambda x, y: np.sqrt((x[0] - y[0])**2. / err_flux**2. + \
        (x[1] - y[1])**2. / err_midtime**2.)

    # Search for clusters a second time, this time to identify the period. We expect
    # a cluster around the mean value and less significant ones around integer
    # multiples of that value.
    try:
        db = DBSCAN(eps=1., min_samples=10, metric=metric).fit(Y[:,0:2])
    except ValueError:
        raise RuntimeError

    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_
    unique_labels = set(labels)
    n_clusters_ = len(unique_labels) - (1 if -1 in labels else 0)

    if n_clusters_ == 1:
        # This is the best-case scenario. The best choice for the period is just
        # the mean of the consecutive differences. The phase and duration follow
        # easily.
        class_member_mask = (labels != -1)

        best_period = np.mean(Y[class_member_mask & core_samples_mask][:,1])
        best_duration = np.amax(Y[class_member_mask & core_samples_mask][:,2])

        if step == 1:
            best_phase = np.mean(np.mod(Y[class_member_mask & core_samples_mask][:,4],
                best_period))
        else:
            best_phase = np.median(np.mod(Y[class_member_mask & core_samples_mask][:,4],
                best_period))
    elif n_clusters_ == 0:
        # No clusters were found at all; let the caller handle this case.
        raise NoClustersError
    else:
        # We need to differentiate between clusters at integer multiples of
        # some period and non-integer multiples. In the integer case, we take
        # the minimum period, otherwise let the caller handle it.
        candidate_periods = []

        for kk in unique_labels:
            if kk == -1:
                continue
            class_member_mask = (labels == kk)
            candidate_periods.append([np.mean(Y[class_member_mask &
                core_samples_mask][:,1]), kk])

        # Check for integer multiples in the candidate periods list. The modulus
        # by the minimum one should be sufficient.
        candidate_periods = np.array(candidate_periods)
        min_period = np.amin(candidate_periods[:,0])
        mods = np.mod(candidate_periods[:,0], min_period)

        ndx = np.where(mods > min_period / 2.)
        mods[ndx] -= min_period

        if np.any(np.absolute(mods) > max_period_err):
            # At least one cluster was not at an integer multiple of the
            # minimum period.
            raise NonIntegerClustersError
        else:
            # All the clusters were at near-integer multiples of the minimum
            # candidate period; use the minimum as the best guess period.
            best_period = candidate_periods[np.argmin(candidate_periods[:,0]),0]
            class_member_mask = (labels ==
                int(candidate_periods[np.argmin(candidate_periods[:,0]),1]))
            best_duration = np.amax(Y[class_member_mask & core_samples_mask][:,2])
            best_phase = np.mean(np.mod(Y[class_member_mask & core_samples_mask][:,4],
                best_period))

    return best_period, best_duration, best_phase


def __do_cluster_plot(db, X):
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_

    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))

    for k, col in zip(unique_labels, colors):
        if k == -1:
            # Black used for noise.
            col = 'k'

        class_member_mask = (labels == k)

        xy = X[class_member_mask & core_samples_mask]
        plt.plot(xy[:,0], xy[:,1], 'o', markerfacecolor=col,
             markeredgecolor='k', markersize=14)

        xy = X[class_member_mask & ~core_samples_mask]
        plt.plot(xy[:,0], xy[:,1], 'o', markerfacecolor=col,
             markeredgecolor='k', markersize=6)

    plt.title('Estimated number of clusters: %d' % n_clusters_)
    plt.show()

