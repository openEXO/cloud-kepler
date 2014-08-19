# -*- coding: utf-8 -*-

import sys
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import scipy.optimize as opt
import scipy.interpolate as interp
import scipy.signal as signal
from sklearn.cluster import DBSCAN
from utils import setup_logging

# Basic logging configuration.
logger = setup_logging(__file__)


class NoClustersError(Exception):
    pass


class NonIntegerClustersError(Exception):
    pass


def clean_signal(time, flux, dtime, dflux, dfluxerr, out, guess_period=None):
    '''
    Remove possible eclipsing binary signals from a light curve. This works
    best on deep, strongly periodic signals, so it is unlikely to clean
    transit signals (though it sometimes will). This should help BLS pulse
    find less prominent signals in the same data.

    :param time: Raw time vector (no detrending or binning)
    :type time: np.ndarray
    :param flux: Raw flux vector (no detrending or binning)
    :type flux: np.ndarray
    :param dtime: Binned and detrended time vector
    :type dtime: np.ndarray
    :param dflux: Binned and detrended flux vector
    :type dflux: np.ndarray
    :param dfluxerr: Binned and detrended flux error vector
    :type dfluxerr: np.ndarray
    :param out: Output from BLS pulse algorithm
    :type out: dict
    '''
    # We restrict the "standard deviation" of the cluster to be 5% of the
    # size of the space.
    size = max(np.nanmax(np.absolute(out['depth_dip'])),
        np.nanmax(out['depth_blip']))
    mean_flux_err = 0.05 * size

    # Construct an array of all the useful quantities. We will only be
    # finding clusters in the first two dimensions! The other dimensions are
    # for bookkeeping.
    ndx = np.where((out['srsq_dip'] > 0.) & (out['srsq_blip'] > 0.))
    X = np.column_stack((out['depth_dip'][ndx], out['depth_blip'][ndx],
        out['duration_dip'][ndx], out['duration_blip'][ndx],
        out['midtime_dip'][ndx], out['midtime_blip'][ndx]))

    metric = lambda x, y: np.sqrt((x[0] - y[0])**2. / mean_flux_err**2. +
        (x[1] - y[1])**2. / mean_flux_err**2.)

    try:
        db = DBSCAN(eps=1., min_samples=10, metric=metric).fit(X[:,0:2])
        #__do_cluster_plot(db, X[:,0:2])
    except ValueError:
        logger.info('Not enough points for DBSCAN to find clusters in the '
            'depth_dip/period space; stopping algorithm.')
        raise RuntimeError

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
        mean_depths.append([np.mean(X[class_member_mask &
            core_samples_mask][:,0]),k])

    mean_depths = np.array(mean_depths)
    ndx = np.argmin(mean_depths[:,0])
    depth = mean_depths[ndx,0]
    k = int(mean_depths[ndx,1])

    # Construct a mask for members of this cluster.
    class_member_mask = (labels == k)

    try:
        best_period, best_duration, best_midtimes = __do_period_search(X, time,
            class_member_mask & core_samples_mask, err_flux=mean_flux_err)
    except NoClustersError:
        # We didn't find any clusters at all. This is a good place to stop.
        logger.info('DBSCAN did not resolve any clusters in the '
            'depth_dip/period space; stopping algorithm.')
        raise RuntimeError
    except NonIntegerClustersError:
        # Something weird is going on. Try one more time with a step of 2,
        # then quit, marking this system for further consideration.
        try:
            best_period, best_duration, best_midtimes = __do_period_search(X,
                time, class_member_mask & core_samples_mask,
                err_flux=mean_flux_err, step=2)
        except (NoClustersError, NonIntegerClustersError):
            logger.warning('DBSCAN found multiple clusters that do not look '
                'like integer multiples; investigate!')
            raise RuntimeError

    # Clean up the best guess period by minimizing "chatter" in the data.
    def chatter(time, flux, P):
        pftime = np.mod(time, P)
        ndx = np.argsort(pftime)

        return np.sum(np.diff(flux[ndx])**2. / np.diff(time[ndx])**2.)

    mask = np.isfinite(dflux)
    res = opt.minimize(lambda x: chatter(dtime[mask], dflux[mask], x),
        best_period, tol=1.e-7, options={'disp':False})
    best_period = res.x[0]

    def smooth(x, window_len):
        s = np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
        w = np.ones(window_len,'d')
        y = np.convolve(w / w.sum(), s, mode='valid')
        return y[(window_len/2-1):-(window_len/2+1)]

    def plavchan(time, flux, period):
        pftime = np.mod(time, period)
        ndx = np.argsort(pftime)
        f = interp.interp1d(pftime[ndx], flux[ndx])
        new_t = np.linspace(time[0], time[-1], time.shape[0])
        new_f = smooth(f(pftime[ndx]), 11)
        f = interp.interp1d(pftime[ndx], new_f)

        chisq = (flux - f(pftime))**2.
        ndx = np.argsort(chisq)
        return np.sum(chisq[ndx][-26:-1])

    best_period = opt.fmin(lambda x: plavchan(dtime[mask], dflux[mask], x),
        best_period, xtol=1.e-6)[0]

    logger.info('Best period: %g' % best_period)
    best_phase = np.median(np.mod(best_midtimes, best_period))

    # Fit the entire transit event with boxcar parameters.
    def boxcar(time, duration, depth, phase, period):
        pftime = np.mod(time - phase - period / 2., period) / period

        flux = np.zeros_like(time)
        mask = ((pftime > 0.5 - 0.5 * duration / period) &
            (pftime < 0.5 + 0.5 * duration / period))
        flux[mask] = depth

        return flux

    p0 = np.array([best_duration, depth, best_phase, best_period],
        dtype='float64')
    logger.info('Best guess boxcar parameters:\n\t' + str(p0))

    ndx = np.where(np.isfinite(dflux))
    f = lambda x: np.sum((dflux[ndx] - boxcar(dtime[ndx], *x))**2.)
    pbest = opt.fmin(f, p0)
    logger.info('Best fit boxcar parameters:\n\t' + str(pbest))

    best_duration = pbest[0]
    best_depth = pbest[1]
    best_phase = pbest[2]
    best_period = pbest[3]

    pftime = np.mod(time - best_phase - best_period / 2., best_period) / best_period
    mask = ((pftime > 0.5 - 2. * best_duration / best_period) &
        (pftime < 0.5 + 2. * best_duration / best_period))
    flux[mask] = np.nan

    return dict(period=best_period, duration=best_duration, depth=best_depth,
        phase=best_phase)


def __do_period_search(X, time, mask, step=1, err_midtime=0.1, err_flux=0.01,
max_period_err=0.1):
    # Remove all samples not in the core of this cluster from the data array.
    # The bookkeeping parameters are still around at this point.
    Y = X[mask][::step]
    Y[0:-1,1] = np.diff(Y[:,4])
    Y = Y[0:-1,:]

    metric = lambda x, y: np.sqrt((x[0] - y[0])**2. / err_flux**2. + \
        (x[1] - y[1])**2. / err_midtime**2.)

    # Search for clusters a second time, this time to identify the period.
    # We expect a cluster around the mean value and less significant ones
    # around integer multiples of that value.
    try:
        db = DBSCAN(eps=1., min_samples=10, metric=metric).fit(Y[:,0:2])
        #__do_cluster_plot(db, Y[:,0:2])
    except ValueError:
        logger.info('Not enough points for DBSCAN to find clusters in the '
            'depth_dip/period space; stopping algorithm.')
        raise RuntimeError

    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_
    unique_labels = set(labels)
    n_clusters_ = len(unique_labels) - (1 if -1 in labels else 0)

    if n_clusters_ == 1:
        # This is the best-case scenario. The best choice for the period is
        # just the mean of the consecutive differences. The phase and
        # duration follow easily.
        class_member_mask = (labels != -1)

        best_period = np.mean(Y[class_member_mask & core_samples_mask][:,1])
        best_duration = np.amax(Y[class_member_mask & core_samples_mask][:,2])
        best_midtimes = Y[class_member_mask & core_samples_mask][:,4]
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

        # Check for integer multiples in the candidate periods list. The
        # modulus by the minimum one should be sufficient.
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
            best_duration = np.amax(Y[class_member_mask &
                core_samples_mask][:,2])
            best_midtimes = Y[class_member_mask & core_samples_mask][:,4]

    return best_period, best_duration, best_midtimes


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

