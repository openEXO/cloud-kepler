#!/usr/bin/env python

from __future__ import division
import sys
import numpy as np
import pandas as pd
from collections import OrderedDict
from PyKE.kepfit import lsqclip
import logging
from common import read_mapper_output, encode_arr

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def detrend_mean_remove(flux, period):
    """Detrend removing the mean of each period

    For each period-length segment, compute and remove the mean flux"""

    def mean_remove(x):
        return x - x.mean()
    segment_ids = np.array(flux.reset_index().time/period).astype(np.int)
    # transform applies a function to each segment
    return flux.groupby(segment_ids).transform(mean_remove)

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
    """Reindexes a series on a 2d matrix of values

    Pandas does not support 2d indexing, so we need to flatten the matrix,
    reindex, and then reshape the result back to 2d.
    """
    return np.array(series.reindex(matrix.flatten())).reshape(matrix.shape)

def compute_signal_residual(binned_segment, matrix, duration, n_bins_min_duration, direction):
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
    i1 = int(SR_index[0])
    i2 = int(matrix[SR_index])
    ## Make sure the best SR matches the desired direction.
    if s[SR_index]*direction >= 0:
        return pd.Series(dict(
                phases=i1,
                durations=binned_segment_indexed.samples[i1:i2].sum(),
                signal_residuals=sr[SR_index]**0.5,
                depths=binned_segment.flux[i1:i2].min(),
                midtimes=0.5*(i1+i2)
                ))
    else:
        return pd.Series(dict(
                phases=np.nan,
                durations=np.nan,
                signal_residuals=np.nan,
                depths=np.nan,
                midtimes=np.nan
                ))


def phase_bin(segment, bins):
    """Phase-bin a light curve segment"""
    grouper = segment.groupby(pd.cut(segment["phase"], bins))
    y = grouper.mean()
    y["samples"] = grouper.time.count()
    del y["segment"]
    return y

def bls_pulse_vec(light_curve, segment_size, min_duration, max_duration, n_bins, detrend_order=None, direction=0, remove_nan_segs=False):
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
    direction : integer
        defines whether transits (-1), anti-transits (+1) or both (0) should be considered, default is both (0)
    
    Returns
    =======
    results : pd.DataFrame
        phase, duration, signal_residual, depth and midtime
    """

    # check inputs
    if segment_size <= 0.0:
        raise ValueError("Segment size must be > 0.")
    if min_duration <= 0.0:
        raise ValueError("Min. duration must be > 0.")
    if max_duration <= min_duration:
        raise ValueError("Max. duration must be > min. duration.")
    if n_bins <= 1:
        raise ValueError("Number of bins must be > 1.")

    n_bins_min_duration = max(np.floor(min_duration/segment_size*n_bins), 1)
    n_bins_max_duration = np.ceil(max_duration/segment_size*n_bins)
    light_curve["segment"] = np.floor(np.array(light_curve.index).astype(np.float)/segment_size)
    light_curve["phase"] = np.remainder(np.array(light_curve.index),segment_size) / segment_size
    sample_rate = np.median(np.diff(np.array(light_curve.index).astype(np.float)))

    if detrend_order:
        detrend_coefficients = {}
        for segment_id, segment_data in light_curve.groupby("segment"):
            if len(segment_data) > 100:
                detrend_coefficients[segment_id], trend = detrend_pyke_lsqclip(segment_data, detrend_order)
                light_curve.flux = light_curve.flux.subtract(trend, fill_value=0.)

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

    results = phase_binned_segments.groupby(level="segment").apply(lambda x:compute_signal_residual(x, matrix=matrix, duration=duration, n_bins_min_duration=n_bins_min_duration, direction=direction))
    if remove_nan_segs: results = results.dropna()
    results["midtimes"] *= segment_size/ n_bins
    results["midtimes"] += light_curve.reset_index().groupby("segment").time.min()
    results["durations"] *= sample_rate * 24.
    if detrend_order:
        return results, detrend_coefficients
    else:
        return results


def main(segment_size, input_string=None, min_duration=0.0416667, max_duration=0.5, n_bins=100,
direction=0, print_format='encoded', verbose=False, detrend_order=None):
    '''
    This is the main routine that allows the vectorized bls_pulse to be called from the
    command line. It takes the same arguments as the corresponding function in bls_pulse.py.
    '''
    # Read in the KIC ID, quarter, and lightcurve data from standard input if it is not
    # supplied through the input options.
    if not input_string:
        input_data = read_mapper_output(sys.stdin)
    else:
        input_data = read_mapper_output(input_string)

    # The return data should be a list (or some other structure) so that we don't stop after
    # the first KIC number.
    return_data = []

    # Peel out the Kepler ID, quarters, and lightcurve form the input data for use.
    # NOTE: The lightcurve is stored as a list of lists comprised of [time, flux, flux_error].
    for k, q, f in input_data:
        kic_id = k
        quarters = q
        lightcurve = f

        # Coerce the lightcurve data into a numpy array, then extract the columns and
        # make a pd.DataFrame for input to vectorized BLS algorithm.
        lc_nparray = np.array(lightcurve)
        time = lc_nparray[:,0]
        flux = lc_nparray[:,1]
        flux_error = lc_nparray[:,2]
        lc = pd.DataFrame(dict(flux=flux, flux_error=flux_error), index=time)
        lc.index.name = 'time'

        temp = bls_pulse_vec(lc, segment_size, min_duration, max_duration, n_bins, 
            detrend_order=detrend_order, direction=direction, remove_nan_segs=False)
        return_data.append(temp)

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
            print "\t".join(map(str, [kic_id, encode_arr(srMax), encode_arr(transitDuration),
                encode_arr(transitDepth), encode_arr(transitMidTime)]))
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

    if len(return_data) == 1:
        return return_data[0]
    else:
        return return_data


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()

