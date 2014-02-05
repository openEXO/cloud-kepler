from __future__ import division
import numpy as np
import pandas as pd
from collections import OrderedDict

def detrend_mean_remove(flux, period):
    """Detrend removing the mean of each period

    For each period-length segment, compute and remove the mean flux"""

    def mean_remove(x):
        return x - x.mean()
    segment_ids = (flux.index/period).astype(np.int)
    # transform applies a function to each segment
    return flux.groupby(segment_ids).transform(mean_remove)

def reindex_to_matrix(series, matrix):
    """Reindexes a series on a 2d matrix of values

    Pandas does not support 2d indexing, so we need to flatten the matrix,
    reindex, and then reshape the result back to 2d.
    """
    return np.array(series.reindex(matrix.flatten())).reshape(matrix.shape)

def bls_vec(light_curve, periods, min_duration, max_duration, n_bins, detrend=detrend_mean_remove):
    """Box Least Square fitting algorithm, vectorized implementation

    Kovacs, 2002

    Parameters
    ==========
    light_curve : pd.DataFrame
        light curve with timing information in days (index), flux and flux error
    periods : list or array
        list of periods to be tested with BLS, for a single period just use [period]
    min_duration, max_duration : float, float
        minimum/maximum duration of the transit as a fraction of period
    n_bins : integer
        number of bins used for binning the folded light curve
    detrend : function
        function to be used for detrending the flux
    
    Returns
    =======
    SR : pd.Series
        Normalized Signal Residual as defined by Kovacs, 2002
    """

    SR = OrderedDict()

    for period in periods:

        n_bins_min_duration = max(np.floor(min_duration*n_bins), 1)
        n_bins_max_duration = np.ceil(max_duration*n_bins)

        phase = np.remainder(np.array(light_curve.index),period) / period
        # pd.cut slices phase in n_bins equally spaced bins
        phase_bins = pd.cut(phase, n_bins)

        detrended_flux = detrend(light_curve, period)

        folded_light_curve = detrended_flux.groupby(phase_bins).mean()
        folded_light_curve["samples"] = light_curve.flux.groupby(phase_bins).count()
        folded_light_curve = folded_light_curve.reset_index()
        
        i1 = np.arange(n_bins - n_bins_min_duration)[:,None]
        dur = np.arange(0, n_bins_max_duration+1)
        matrix = i1 + dur
        # matrix is the grid of indices to be used for evaluating SR
        # i1 is vertical, i2 is horizontal
        # each row is a segment, for example row 2 has bin indices from 2 to 6
        # 1 2 3 4 5
        # 2 3 4 5 6
        # 3 4 5 6 7

        # evaluates sr on a grid of values in a single step (loop with C performance)
        r = reindex_to_matrix(folded_light_curve.samples, matrix).cumsum(axis=1)
        s = reindex_to_matrix(folded_light_curve.flux, matrix).cumsum(axis=1)
        sr = s**2 / (r * (len(light_curve) - r))

        sr[:,dur <= n_bins_min_duration] = np.nan

        SR[period] = np.ma.masked_invalid(sr).max()

    SR = pd.Series(SR)
    SR = SR**0.5
    SR /= SR.max()
    return SR
