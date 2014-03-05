from __future__ import division
import numpy as np
import pandas as pd
from collections import OrderedDict
import exceptions

def detrend_mean_remove(flux, period):
    """Detrend removing the mean of each period

    For each period-length segment, compute and remove the mean flux"""

    def mean_remove(x):
        return x - x.mean()
    segment_ids = np.array(flux.reset_index().time/period).astype(np.int)
    # transform applies a function to each segment
    return flux.groupby(segment_ids).transform(mean_remove)

def reindex_to_matrix(series, matrix):
    """Reindexes a series on a 2d matrix of values

    Pandas does not support 2d indexing, so we need to flatten the matrix,
    reindex, and then reshape the result back to 2d.
    """
    return np.array(series.reindex(matrix.flatten())).reshape(matrix.shape)

def compute_signal_residual(binned_segment, matrix, duration, n_bins_min_duration):
    """Run BLS algorithm on a binned segment
    
    Returns
    -------
    phase, duration, signal_residual, depth and midtime"""
    binned_segment_indexed = binned_segment.reset_index(drop=True)
    r = reindex_to_matrix(binned_segment_indexed.samples, matrix).cumsum(axis=1)
    s = reindex_to_matrix(binned_segment_indexed.flux, matrix).cumsum(axis=1)
    n = binned_segment_indexed.samples.sum()
    sr = s**2 / (r * (n - r))

    sr[:,duration <= n_bins_min_duration] = np.nan
    SR_index = np.unravel_index(np.ma.masked_invalid(sr).argmax(), sr.shape)
    i1 = SR_index[0]
    i2 = matrix[SR_index]
    return pd.Series(dict(
                phase=i1,
                duration=i2-i1+1,
                signal_residual=sr[SR_index]**0.5,
                depth=-s[SR_index]*n/(r[SR_index]*(n-r[SR_index])), 
                midtime=0.5*(i1+i2)
                    ))


def phase_bin(segment, bins):
    """Phase-bin a light curve segment"""
    grouper = segment.groupby(pd.cut(segment["phase"], bins))
    y = grouper.mean()
    y["samples"] = grouper.time.count()
    del y["segment"]
    return y

def bls_pulse_vec(light_curve, segment_size, min_duration, max_duration, n_bins, detrend=detrend_mean_remove):
    """Box Least Square fitting algorithm, vectorized implementation

    Kovacs, 2002

    Parameters
    ==========
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
    
    Returns
    =======
    results : pd.DataFrame
        phase, duration, signal_residual, depth and midtime
    """

    # check inputs
    if segment_size <= 0.0:
        raise exceptions.ValueError("Segment size must be > 0.")
    if min_duration <= 0.0:
        raise exceptions.ValueError("Min. duration must be > 0.")
    if max_duration <= min_duration:
        raise exceptions.ValueError("Max. duration must be > min. duration.")
    if n_bins <= 1:
        raise exceptions.ValueError("Number of bins must be > 1.")

    n_bins_min_duration = max(np.floor(min_duration/segment_size*n_bins), 1)
    n_bins_max_duration = np.ceil(max_duration/segment_size*n_bins)
    light_curve["segment"] = np.floor(np.array(light_curve.index).astype(np.float)/segment_size)
    light_curve["phase"] = np.remainder(np.array(light_curve.index),segment_size) / segment_size

    # define equally spaced bins
    bins = np.linspace(0, 1, num=n_bins)

    phase_binned_segments = light_curve.reset_index().groupby("segment").apply(lambda x:phase_bin(x, bins=bins))

    i1 = np.arange(n_bins - n_bins_min_duration)[:,None]
    duration = np.arange(0, n_bins_max_duration)
    matrix = i1 + duration
    # matrix is the grid of indices to be used for evaluating SR
    # i1 is vertical, i2 is horizontal
    # each row is a segment, for example row 2 has bin indices from 2 to 6
    # 1 2 3 4 5
    # 2 3 4 5 6
    # 3 4 5 6 7

    results = phase_binned_segments.groupby(level="segment").apply(lambda x:compute_signal_residual(x, matrix=matrix, duration=duration, n_bins_min_duration=n_bins_min_duration))
    results = results.dropna()
    results["midtime"] *= segment_size/ n_bins
    results["midtime"] += light_curve.reset_index().groupby("segment").time.min()
    return results
