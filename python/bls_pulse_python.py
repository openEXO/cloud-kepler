# -*- coding: utf-8 -*-

'''
BLS_PULSE algorithm, based on ``bls_pulse.pro`` originally written by Peter
McCullough.
'''

import numpy as np
from utils import setup_logging

# Basic logging configuration.
logger = setup_logging(__file__)


def __convert_duration_to_bins(duration_days, nbins, segment_size,
duration_type):
    '''
    Converts the requested duration (in days) to a duration in (full) units of
    bins. Rounds down for min and round up for max.

    :param duration_days: Duration to convert in days
    :type duration_days: float
    :param nbins: Number of bins in a segment
    :type nbins: int
    :param segment_size: Size of a segment in days
    :type segment_size: float
    :param duration_type: Type of duration to calculate. Valid values are `min`
        and `max`
    :type duration_type: str

    :rtype: float
    '''
    if duration_type == 'min':
        # This was the way it was calculated originally.
        # duration_bins = max(int(duration_days*nbins/segment_size),1)
        # Here is SWF's version as he understands it.
        duration_bins = max(int(np.floor(duration_days*nbins/segment_size)),1)
    elif duration_type == 'max':
        # This was the way it was calculated originally.
        # duration_bins = max(int(duration_days*nbins/segment_size),1)
        # Here is SWF's version as he understands it.
        duration_bins = max(1,
            min(int(np.ceil(duration_days*nbins/segment_size)), nbins))
    else:
        # Note (SWF): Need to add proper error handler here.
        raise ValueError('Invliad duration type: %s' % duration_type)

    return duration_bins


def __calc_sr_max(n, nbins, mindur, maxdur, direction, binTime, binFlx, ppb):
    '''
    Calculates the maximum signal residual for a given segment.

    :param n: Total number of points that were binned to this segment
    :type n: int
    :param nbins: Number of bins in each segment
    :type nbins: int
    :param mindur: Minimum signal duration to accept, in units of bins
    :type mindur: int
    :param maxdur: Maximum signal duration to accept, in units of bins
    :type maxdur: int
    :param direction: Signal direction to accept; -1 for dips, +1 for blips, or
        0 for best
    :type direction: int
    :param binTime: Array of binned times
    :type binTime: numpy.ndarray
    :param binFlx: Array of binned fluxes
    :type binFlx: numpy.ndarray
    :param ppb: Weights for each bin; each weight is the number of points that
        were binned to the corresponding bin
    :type ppb: numpy.ndarray

    :rtype: tuple
    '''
    # Note (SWF):  I want to double check the math here matches what is done in
    # Kovacs et al. (2002).  On the TO-DO list...

    # Initialize output values to NaN.
    sr = np.nan
    thisDuration = np.nan
    thisDepth = np.nan
    thisMidTime = np.nan

    # Initialize the "best" Signal Residue to NaN.
    best_SR = np.nan

    for i1 in range(nbins):
        s = 0; r = 0
        curDepth = binFlx[i1]

        for i2 in range(i1, min(i1 + maxdur + 1,nbins)):
            s += binFlx[i2]
            r += ppb[i2]

            if i2 - i1 >= mindur and direction * s >= 0 and r < n:
                sr = s**2 / (r * (n - r))

                if sr > best_SR or np.isnan(best_SR):
                    # Update the best SR values.
                    best_SR = sr

                    # Report the duration in units of days, not bins.
                    thisDuration = binTime[i2] - binTime[i1]

                    # Update the depth.
                    thisDepth = (s / r) + (s / (n - r))

                    # Report the transit midtime in units of days.
                    thisMidTime = (binTime[i2] + binTime[i1]) / 2.

    # Return a tuple containing the Signal Residue and corresponding signal
    # information. If no Signal Residue was calculated in the loop above, then
    # these will all be NaN's.
    return (best_SR, thisDuration, thisDepth, thisMidTime)


def bls_pulse(time, flux, fluxerr, n_bins, segment_size, min_duration,
max_duration, direction=0, detrend_order=0):
    '''
    Main function for this module; performs the BLS pulse algorithm on the input
    lightcurve data. Lightcurve should be 0-based if no detrending is used.

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
    :param direction: Signal direction to accept; -1 for dips, +1 for blips, or
        0 for best
    :type direction: int
    :param detrend_order: Order of detrending to use on input; 0 for no
        detrending
    :type detrend_order: int

    :rtype: dict
    '''
    # The number of bins can sometimes change, so make a working copy so that
    # the original value is still available.
    nbins = n_bins

    # Calculate the time baseline of this lightcurve (this will be in days).
    lightcurve_timebaseline = time[-1] - time[0]

    # Convert the min and max transit durations to units of bins from units of
    # days.
    mindur = __convert_duration_to_bins(min_duration, nbins, segment_size,
        duration_type="min")
    maxdur = __convert_duration_to_bins(max_duration, nbins, segment_size,
        duration_type="max")

    # Extract lightcurve information and mold it into numpy arrays.
    # First identify which elements are not finite and remove them.
    ndx = np.isfinite(flux)
    time = time[ndx]
    flux = flux[ndx]

    # Divide the input time and flux arrays into segments.
    nsegments = int(np.floor((np.amax(time) - np.amin(time)) /
        segment_size) + 1.)
    segments = [(q,time[(time >= q*segment_size) & (time < (q+1)*segment_size)])
        for q in xrange(nsegments)]
    flux_segments = [(q,flux[(time >= q*segment_size) &
        (time < (q+1)*segment_size)]) for q in xrange(nsegments)]

    # Initialize storage arrays for output values.  We don't know how many
    # signals we will find, so for now these are instantiated without a length
    # and we make use of the (more inefficient) "append" method in numpy to
    # grow the array.  This could be one area that could be made more efficient
    # if speed is a concern, e.g., by making these a sufficiently large size,
    # filling them in starting from the first index, and then remove those that
    # are empty at the end.  A sufficiently large size could be something like
    # the time baseline of the lightcurve divided by the min. transit duration
    # being considered, for example.
    # I think we sort of do now how long they are going to be, we are finding
    # the best signal for each segment so it'll come out equal to the number of
    # segments. It was just programmed this way, probably inefficient though.
    srMax = np.array([], dtype='float64')
    transitDuration = np.array([], dtype='float64')
    transitMidTime = np.array([], dtype='float64')
    transitDepth = np.array([], dtype='float64')

    # For each segment of this lightcurve, bin the data points into appropriate
    # segments, normalize the binned fluxes, and calculate SR_Max.  If the new
    # SR value is greater than the previous SR_Max value, store it as a
    # potential signal.
    # NOTE: "sr" is the Signal Residue as defined in the original BLS paper by
    # Kovacs et al. (2002), A&A, 391, 377.
    for jj,seg,flux_seg in zip(range(len(segments)),segments,flux_segments):
        # Default this segment's output values to NaN.  If a valid SR_Max is
        # found, these will be updated with finite values.
        srMax = np.append(srMax, np.nan)
        transitDuration = np.append(transitDuration, np.nan)
        transitMidTime = np.append(transitMidTime, np.nan)
        transitDepth = np.append(transitDepth, np.nan)

        # Bin the data points.  First extract the segment number and segment
        # array, then count how many points in this segment.
        l,this_seg = seg
        ll,this_flux_seg = flux_seg
        n = this_seg.size

        # Make sure the number of bins is not greater than the number of data
        # points in this segment.
        nbins = int(n_bins)
        if n < nbins:
            nbins = n
            mindur = __convert_duration_to_bins(min_duration, nbins,
                segment_size, duration_type="min")
            maxdur = __convert_duration_to_bins(max_duration, nbins,
                segment_size, duration_type="max")

        # NOTE: Modified by emprice.
        # See http://stackoverflow.com/questions/6163334/binning-data-in-python-with-scipy-numpy
        # Compute average times and fluxes in each bin, and count the number of
        # points per bin.
        bin_slices = np.linspace(float(jj) * segment_size, float(jj + 1) *
            segment_size, nbins+1)
        bin_memberships = np.digitize(this_seg, bin_slices)
        binned_times = [this_seg[bin_memberships == i].mean() for i in range(1,
            len(bin_slices))]
        binned_fluxes = [this_flux_seg[bin_memberships == i].mean() for i in
            range(1, len(bin_slices))]
        ppb = [len(this_seg[bin_memberships == i]) for i in range(1,
            len(bin_slices))]

        # TODO: Detrending!

        # Determine SR_Max.  The return tuple consists of:
        #      (Signal Residue, Signal Duration, Signal Depth, Signal MidTime)
        sr_tuple = __calc_sr_max(n, nbins, mindur, maxdur, direction,
            binned_times, binned_fluxes, ppb)

        # If the Signal Residue is finite, then we need to add these parameters
        # to our output storage array.
        if np.isfinite(sr_tuple[0]):
            srMax[-1] = sr_tuple[0]
            transitDuration[-1] = sr_tuple[1]
            transitDepth[-1] = sr_tuple[2]
            transitMidTime[-1] = sr_tuple[3]

    # Return each segment's best transit event.  Create a pandas data frame
    # based on the array of srMax and transit parameters.  The index of the
    # pandas array will be the segment number.
    return_data = dict(srsq=srMax, duration=transitDuration, depth=transitDepth,
        midtime=transitMidTime)
    return return_data


if __name__ == "__main__":
    main()

