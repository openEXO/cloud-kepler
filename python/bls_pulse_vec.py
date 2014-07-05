#!/usr/bin/env python

from __future__ import division
import sys
import numpy as np
import pandas as pd
from collections import OrderedDict
from PyKE.kepfit import lsqclip
import logging
from utils import extreme

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def detrend_mean_remove(flux, period):
    '''
    Detrend removing the mean of each period. For each period-length segment, compute
    and remove the mean flux.
    '''
    segment_ids = np.floor(np.array(flux.reset_index().time/period))

    # Transform applies a function to each segment
    return flux.flux.groupby(segment_ids).transform(lambda x: x - x.mean())


def detrend_pyke_lsqclip(segment, order):
    functype = 'poly' + str(order)
    pinit = np.zeros(order + 1, dtype=np.float)
    pinit[0] = segment.flux.mean()

    sigma_threshold = 3
    niter = 3
    logfile = "kepler.log"
    verbose = True
    time = np.array(segment.index).astype(np.double)
    coeffs, errors, covar, iiter, sigma, chi2, dof, fit, plotx1, ploty1, status = \
    lsqclip(functype, pinit, time, np.array(segment.flux),
            np.array(segment.flux_error),
            sigma_threshold, sigma_threshold, niter, logfile, verbose)
    trend = pd.Series(np.polyval(coeffs[::-1], time), index=segment.index)

    return coeffs[::-1], trend


def reindex_to_matrix(series, matrix):
    '''
    Reindexes a series on a 2d matrix of values. Pandas does not support 2d indexing,
    so we need to flatten the matrix, reindex, and then reshape the result back to 2d.
    '''
    return np.array(series.reindex(matrix.flatten())).reshape(matrix.shape)


def compute_signal_residual(binned_segment, matrix, duration, n_bins_min_duration, direction):
    '''
    Run BLS algorithm on a binned segment.

    Returns: phase, duration, signal_residual, depth, and midtime
    '''
    binned_segment_indexed = binned_segment.reset_index(drop=True)
    r = reindex_to_matrix(binned_segment_indexed.samples, matrix).cumsum(axis=1)
    s = reindex_to_matrix(binned_segment_indexed.flux, matrix).cumsum(axis=1)
    n = binned_segment_indexed.samples.sum()
    sr = s**2 / (r * (n - r))

    # NOTE: Modified by emprice. Durations can be the minimum value but not smaller.
    sr[:,duration < n_bins_min_duration] = np.nan
    SR_index = np.unravel_index(np.ma.masked_invalid(sr).argmax(), sr.shape)
    i1 = int(SR_index[0])
    i2 = int(matrix[SR_index])

    # Make sure the best SR matches the desired direction.
    if s[SR_index]*direction >= 0:
        return pd.Series(dict(phases=i1,
            durations=(binned_segment.time.values[i2]-binned_segment.time.values[i1]),
            signal_residuals=sr[SR_index],
            depths=extreme(binned_segment.flux[i1:i2+1].values, direction),
            midtimes=0.5*(binned_segment.time.values[i1]+binned_segment.time.values[i2])))
    else:
        return pd.Series(dict(phases=np.nan, durations=np.nan, signal_residuals=np.nan,
            depths=np.nan, midtimes=np.nan))


def phase_bin(segment, bins):
    '''
    Phase-bin a light curve segment.
    '''
    # NOTE: emprice added `right` option to emualte behavior of other binning schemes.
    grouper = segment.groupby(pd.cut(segment['phase'], bins, right=False))
    y = grouper.mean()
    y["samples"] = grouper.time.count()
    del y["segment"]
    return y


def bls_pulse(time, flux, fluxerr, n_bins, segment_size, min_duration, max_duration,
detrend_order=None, direction=0, remove_nan_segs=False):
    '''
    Box Least Square fitting algorithm, vectorized implementation. See Kovacs et al. (2002)

    Inputs:
      light_curve : pd.DataFrame
        light curve with timing information in days (index), flux and flux error
      segment_size : float
        segment_size to be tested with BLS
      min_duration, max_duration : float, float
        minimum/maximum duration of the transit in days
      n_bins : integer
        number of bins used for binning the folded light curve
      detrend : function
        function to be used for detrending the flux
      direction : integer
        defines whether transits (-1), anti-transits (+1) or both (0) should be considered,
        default is both (0)

    Returns:
      results : pd.DataFrame
        phase, duration, signal_residual, depth and midtime
    '''
    if segment_size <= 0.0:
        raise ValueError("Segment size must be > 0.")
    if min_duration <= 0.0:
        raise ValueError("Min. duration must be > 0.")
    if max_duration <= min_duration:
        raise ValueError("Max. duration must be > min. duration.")
    if n_bins <= 1:
        raise ValueError("Number of bins must be > 1.")

    light_curve = pd.DataFrame(data=np.column_stack((flux,fluxerr)), index=time,
        columns=['flux','flux_error'])
    light_curve.index.name = 'time'

    n_bins_min_duration = max(np.floor(min_duration/segment_size*n_bins), 1)
    n_bins_max_duration = np.ceil(max_duration/segment_size*n_bins)
    light_curve["segment"] = np.floor(np.array(light_curve.index).astype(np.float)/segment_size)
    light_curve["phase"] = np.remainder(np.array(light_curve.index),segment_size) / segment_size
    sample_rate = np.median(np.diff(np.array(light_curve.index).astype(np.float)))

    # TODO: Detrending!

    # Define equally spaced bins and bin according to phase.
    bins = np.linspace(0., 1., n_bins+1)
    phase_binned_segments = light_curve.reset_index().groupby('segment').apply(lambda x:
        phase_bin(x, bins=bins))

    i1 = np.arange(n_bins - n_bins_min_duration)[:,None]
    duration = np.arange(0, n_bins_max_duration)

    # matrix is the grid of indices to be used for evaluating SR
    # i1 is vertical, i2 is horizontal
    # each row is a segment, for example row 2 has bin indices from 2 to 6
    # 1 2 3 4 5
    # 2 3 4 5 6
    # 3 4 5 6 7
    matrix = i1 + duration

    results = phase_binned_segments.groupby(level="segment").apply(lambda x:
        compute_signal_residual(x, matrix=matrix, duration=duration,
        n_bins_min_duration=n_bins_min_duration, direction=direction))

    if remove_nan_segs:
        results = results.dropna()

    return_data = dict(srsq=results.signal_residuals.values,
        duration=results.durations.values, depth=results.depths.values,
        midtime=results.midtimes.values)

    if detrend_order:
        return return_data, detrend_coefficients
    else:
        return return_data


def bls_pulse_main(time, flux, fluxerr, n_bins, segment_size, min_duration, max_duration,
direction=0, print_format='none', verbose=False, detrend_order=None):
    '''
    This is the main routine that allows the vectorized bls_pulse to be called from the
    command line. It takes the same arguments as the corresponding function in bls_pulse.py.
    '''
    lc = pd.DataFrame(dict(flux=flux, flux_error=flux_error), index=time)
    lc.index.name = 'time'

    temp = bls_pulse_vec(lc, segment_size, min_duration, max_duration, n_bins,
        detrend_order=detrend_order, direction=direction, remove_nan_segs=False)

    if type(temp) is tuple:
        # Depending on the detrending used, `temp` may be a tuple or a DataFrame;
        # take only the first element if there is more than one.
        temp = temp[0]

    # Return format is DataFrame; NumPy arrays are easier to work with here.
    srMax = temp['signal_residuals'].as_matrix()
    transitDuration = temp['durations'].as_matrix()
    transitDepth = temp['depths'].as_matrix()
    transitMidTime = temp['midtimes'].as_matrix()
    segments = temp.index

    if print_format == 'encoded':
        print "\t".join(map(str, [kic_id, encode_arr(srMax), encode_array(transitDuration),
            encode_array(transitDepth), encode_array(transitMidTime)]))
    elif print_format == 'normal':
        print '-' * 80
        print 'Kepler ' + kic_id
        print 'Quarters: ' + quarters
        print '-' * 80
        print '{0: <7s} {1: <13s} {2: <10s} {3: <9s} {4: <13s}'.format('Segment',
            'srMax', 'Duration', 'Depth', 'MidTime')

        for ii, seq in enumerate(segments):
            print '{0: <7d} {1: <13.6f} {2: <10.6f} {3: <9.6f} {4: <13.6f}'.format(ii,
                srMax[ii], transitDuration[ii], transitDepth[ii], transitMidTime[ii])

        print '-' * 80
        print

    return temp


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()

