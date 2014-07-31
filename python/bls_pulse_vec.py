#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import sys
import numpy as np
import pandas as pd
from collections import OrderedDict
from PyKE.kepfit import lsqclip
from utils import extreme_vec as extreme, setup_logging

# Basic logging configuration.
logger = setup_logging(__file__)


def __reindex_to_matrix(series, matrix):
    '''
    Reindexes a series on a 2d matrix of values. Pandas does not support 2d indexing,
    so we need to flatten the matrix, reindex, and then reshape the result back to 2d.

    :param series: Array to reindex
    :type series: pandas.Series
    :param matrix: Reindexing matrix
    :type matrix: numpy.ndarray

    :rtype: numpy.ndarray
    '''
    return np.array(series.reindex(matrix.flatten())).reshape(matrix.shape)


def __compute_signal_residual(binned_segment, matrix, duration, n_bins_min_duration, direction):
    '''
    Run BLS algorithm on a binned segment.

    :param binned_segment: Segment for which to calculate the residual
    :type binned_segment: pandas.DataFrame
    :param matrx: Matrix of i1, i2 indices
    :type matrix: numpy.ndarray
    :param duration: Array of durations to consider
    :type duration: numpy.ndarray
    :param n_bins_min_duration: Length of minimum duration in full bins
    :type n_bins_min_duration: int
    :param direction: Signal direction to accept; -1 for dips, +1 for blips, or 0
        for best
    :type direction: int

    :rtype: pandas.Series
    '''
    binned_segment_indexed = binned_segment.reset_index(drop=True)
    r = __reindex_to_matrix(binned_segment_indexed.samples, matrix).cumsum(axis=1)
    s = __reindex_to_matrix(binned_segment_indexed.flux, matrix).cumsum(axis=1)
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
            depths=extreme(binned_segment.flux[i1:i2+1].values),
            midtimes=0.5*(binned_segment.time.values[i1]+binned_segment.time.values[i2])))
    else:
        return pd.Series(dict(phases=np.nan, durations=np.nan, signal_residuals=np.nan,
            depths=np.nan, midtimes=np.nan))


def __phase_bin(segment, bins):
    '''
    Phase-bin a light curve segment.

    :param segment: Segment to bin
    :type segment: pandas.DataFrame
    :param bins: Array of bin edges to use
    :type bins: numpy.ndarray

    :rtype: pandas.DataFrame
    '''
    # NOTE: emprice added `right` option to emualte behavior of other binning schemes.
    grouper = segment.groupby(pd.cut(segment['phase'], bins, right=False))
    y = grouper.mean()
    y["samples"] = grouper.time.count()
    del y["segment"]
    return y


def bls_pulse(time, flux, fluxerr, n_bins, segment_size, min_duration, max_duration,
detrend_order=3, direction=0, remove_nan_segs=False):
    '''
    Main function for this module; performs the BLS pulse algorithm on the input
    lightcurve data, in a vectorized way. Lightcurve should be 0-based if no
    detrending is used.

    See Kovacs et al. (2002)

    :param time: Array of times of observations; nominally in units of days
    :type time: numpy.ndarray
    :param flux: Array of fluxes corresponding to times
    :type flux: numpy.ndarray
    :param fluxerr: Array of flux errors corresponding to times
    :type fluxerr: numpy.ndarray
    :param n_bins: Number of bins in each segment
    :type n_bins: int
    :param segment_size: Length of a segment, in days
    :type segment_size: float
    :param min_duration: Minimum signal duration to accept, in days
    :type min_duration: float
    :param max_duration: Maximum signal duration to accept, in days
    :type max_duration: float
    :param direction: Signal direction to accept; -1 for dips, +1 for blips, or 0
        for best
    :type direction: int
    :param detrend_order: Order of detrending to use on input; 0 for no detrending
    :type detrend_order: int
    :param remove_nan_segs: Remove from the output segments with no accepted events
    :type remove_nan_segs: bool

    :rtype: dict
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
        __phase_bin(x, bins=bins))

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
        __compute_signal_residual(x, matrix=matrix, duration=duration,
        n_bins_min_duration=n_bins_min_duration, direction=direction))

    if remove_nan_segs:
        results = results.dropna()

    return_data = dict(srsq=results.signal_residuals.values,
        duration=results.durations.values, depth=results.depths.values,
        midtime=results.midtimes.values)

    return return_data

