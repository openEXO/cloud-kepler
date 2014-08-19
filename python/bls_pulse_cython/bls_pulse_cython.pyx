# -*- coding: utf-8 -*-

import numpy as np
from detrend import polyfit
from numpy.polynomial import polynomial as poly
cimport numpy as np
cimport cython


cdef extern int do_bls_pulse_segment(double *time, double *flux, double *fluxerr, double *samples,
    int nbins, int n, int nbins_min_dur, int nbins_max_dur, int direction, double *srsq,
    double *duration, double *depth, double *midtime)

cdef extern int do_bls_pulse_segment_compound(double *time, double *flux, double *fluxerr,
    double *samples, int nbins, int n, int nbins_min_dur, int nbins_max_dur,
    double *srsq_dip, double *duration_dip, double *depth_dip, double *midtime_dip,
    double *srsq_blip, double *duration_blip, double *depth_blip, double *midtime_blip)

cdef extern int do_bin_segment(double *time, double *flux, double *fluxerr, int nbins,
    double segsize, int nsamples, int n, int *ndx, double *stime, double *sflux,
    double *sfluxerr, double *samples, double *start, double *end)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
@cython.embedsignature(True)
def bls_pulse(np.ndarray[double, ndim=1, mode='c'] time,
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr,
np.ndarray[double, ndim=1, mode='c'] samples, int nbins, double segsize, double mindur,
double maxdur, direction=0):
    cdef int i, nsamples, nsegments
    cdef np.ndarray[double, ndim=1, mode='c'] stime, sflux, sfluxerr, ssamples
    cdef np.ndarray[double, ndim=2, mode='c'] srsq, depth, duration, midtime
    cdef np.ndarray[double, ndim=2, mode='c'] srsq_dip, depth_dip, duration_dip, midtime_dip
    cdef np.ndarray[double, ndim=2, mode='c'] srsq_blip, depth_blip, duration_blip, midtime_blip

    # Prepare the lightcurve so that it meets our assumptions.
    t = np.nanmin(time)
    time -= t

    nsamples = np.size(time)
    nsegments = np.floor(np.nanmax(time) / segsize) + 1

    if direction == 2:
        srsq_dip = np.empty((nsegments,nbins), dtype='float64')
        duration_dip = np.empty((nsegments,nbins), dtype='float64')
        depth_dip = np.empty((nsegments,nbins), dtype='float64')
        midtime_dip = np.empty((nsegments,nbins), dtype='float64')
        srsq_blip = np.empty((nsegments,nbins), dtype='float64')
        duration_blip = np.empty((nsegments,nbins), dtype='float64')
        depth_blip = np.empty((nsegments,nbins), dtype='float64')
        midtime_blip = np.empty((nsegments,nbins), dtype='float64')
    else:
        srsq = np.empty((nsegments,nbins), dtype='float64')
        duration = np.empty((nsegments,nbins), dtype='float64')
        depth = np.empty((nsegments,nbins), dtype='float64')
        midtime = np.empty((nsegments,nbins), dtype='float64')

    for i in xrange(nsegments):
        # Set up a view for each segment.
        ndx = i * nbins
        stime = time[ndx:ndx+nbins]
        sflux = flux[ndx:ndx+nbins]
        sfluxerr = fluxerr[ndx:ndx+nbins]
        ssamples = samples[ndx:ndx+nbins]

        # Call the algorithm.
        if direction == 2:
            __bls_pulse_binned_compound(stime, sflux, sfluxerr, ssamples, segsize, mindur,
                maxdur, srsq_dip[i,:], duration_dip[i,:], depth_dip[i,:], midtime_dip[i,:],
                srsq_blip[i,:], duration_blip[i,:], depth_blip[i,:], midtime_blip[i,:])
        else:
            __bls_pulse_binned(stime, sflux, sfluxerr, ssamples, segsize, mindur, maxdur,
                direction, srsq[i,:], duration[i,:], depth[i,:], midtime[i,:])

    # Fix the time offset (subtracted off earlier).
    time += t

    if direction == 2:
        midtime_dip += t
        midtime_blip += t

        # Maximize over the bin axis.
        ndx1 = np.nanargmax(srsq_dip, axis=1)
        ind1 = np.indices(ndx1.shape)
        ndx2 = np.nanargmax(srsq_blip, axis=1)
        ind2 = np.indices(ndx2.shape)

        return dict(srsq_dip=srsq_dip[ind1,ndx1].ravel(),
            duration_dip=duration_dip[ind1,ndx1].ravel(),
            depth_dip=depth_dip[ind1,ndx1].ravel(),
            midtime_dip=midtime_dip[ind1,ndx1].ravel(),
            srsq_blip=srsq_blip[ind2,ndx2].ravel(),
            duration_blip=duration_blip[ind2,ndx2].ravel(),
            depth_blip=depth_blip[ind2,ndx2].ravel(),
            midtime_blip=midtime_blip[ind2,ndx2].ravel())
    else:
        midtime += t

        # Maximize over the bin axis.
        ndx = np.nanargmax(srsq, axis=1)
        ind = np.indices(ndx.shape)

        return dict(srsq=srsq[ind,ndx].ravel(),
            duration=duration[ind,ndx].ravel(),
            depth=depth[ind,ndx].ravel(),
            midtime=midtime[ind,ndx].ravel())


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
@cython.embedsignature(True)
def bin_and_detrend(np.ndarray[double, ndim=1, mode='c'] time,
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr,
int nbins, double segsize, int detrend_order=3, int maxgap=100):
    '''
    Bin and detrend a full dataset (time, flux, and error). Binning takes place
    in O(N) time; time to detrend will scale with both N and `detrend_order`.

    :param time: Array of observation times
    :type time: np.ndarray
    :param flux: Array of fluxes observed at `times`
    :type flux: np.ndarray
    :param fluxerr: Array of flux errors observed at `times`
    :type fluxerr: np.ndarray
    :param nbins: Number of bins in each segment
    :type nbins: int
    :param segsize: Size of each segment, in the same time units as `times`
    :type segsize: float
    :param detrend_order: Order of the polynomial to fit for detrending
    :type detrend_order: int
    '''
    cdef double start, end, t
    cdef int nsamples, nsegments, save, i, j
    cdef int gapcount, ingap, dstart_, dend_, x, y, w, z
    cdef np.ndarray[double, ndim=1, mode='c'] btime, bflux, bfluxerr, bsamples
    cdef np.ndarray[double, ndim=1, mode='c'] dflux, dfluxerr, trend
    cdef np.ndarray[double, ndim=1, mode='c'] stime, sflux, sfluxerr, ssamples
    cdef np.ndarray[double, ndim=1, mode='c'] stime_extend, sflux_extend, sfluxerr_extend
    cdef np.ndarray[double, ndim=1, mode='c'] segstart, segend

    t = np.nanmin(time)
    time -= t

    nsamples = np.size(time)
    nsegments = int(np.floor(np.nanmax(time) / segsize) + 1)
    save = 0

    # Arrays for the binned data and sample counts
    btime = np.zeros((nsegments*nbins,), dtype='float64')
    bflux = np.zeros((nsegments*nbins,), dtype='float64')
    bfluxerr = np.zeros((nsegments*nbins,), dtype='float64')
    bsamples = np.zeros((nsegments*nbins,), dtype='float64')

    # Arrays for the detrended data. Note that we don't change the time
    # axis when we detrend, so there is no need for a `dtime` array.
    dflux = np.empty((nsegments*nbins,), dtype='float64')
    dfluxerr = np.empty((nsegments*nbins,), dtype='float64')
    dflux[:] = np.nan
    dfluxerr[:] = np.nan

    # Array to store detrending coefficients.
    coeffs = np.empty((nsegments,detrend_order+1), dtype='float64')

    # Other preallocated arrays; store segment start/end times and a flag
    # for segments that should not be used.
    segstart = np.empty((nsegments,), dtype='float64')
    segend = np.empty((nsegments,), dtype='float64')

    for i in xrange(nsegments):
        j = nbins * i

        # Construct views onto the binned arrays. These will contain the binned
        # times, fluxes, errors, and sample counts for this segment alone.
        stime = btime[j:j+nbins]
        sflux = bflux[j:j+nbins]
        sfluxerr = bfluxerr[j:j+nbins]
        ssamples = bsamples[j:j+nbins]

        # Perform the actual binning. This function writes directly to the
        # binned arrays in memory. The variable `save` keeps up with the index
        # of the next segment start so that we can bin in O(N) time (only need
        # to loop through the array once). This is also why the entire array is
        # binned and detrended at once.
        do_bin_segment(&time[0], &flux[0], &fluxerr[0], nbins, segsize,
            nsamples, i, &save, &stime[0], &sflux[0], &sfluxerr[0],
            &ssamples[0], &start, &end)

        # Correct the segment start and end times by the constant offset found
        # earlier so they are on the same scale as the input time.
        segstart[i] = start + t
        segend[i] = end + t

    if detrend_order == 0:
        # No detrending required; return the binned arrays instead.
        return btime, bflux, bfluxerr, bsamples, segstart, segend

    # Initialize these parameters reasonably; they will all be overwritten
    # in the loop, but initializing `gapcount` to 0 is very important!
    ingap = True
    gapcount = 0
    dstart_ = 0
    dend_ = 0

    for i in xrange(nsegments*nbins):
        if np.isnan(bflux[i]):
            gapcount += 1
        else:
            gapcount = 0

            if ingap:
                ingap = False
                dstart_ = i
            else:
                dend_ = i

        if gapcount > maxgap and not ingap and dstart_ < dend_:
            # We have reached a gap, so the data between `dstart_` and `dend_`
            # should be valid.
            ingap = True

            try:
                ns = int(np.floor((np.nanmax(btime[dstart_:dend_]) -
                    np.nanmin(btime[dstart_:dend_])) / segsize) + 1)
            except ValueError:
                raise ValueError(' '.join([str(btime[dstart_:dend_]), str(dstart_), str(dend_)]))

            for j in xrange(ns):
                x = max(dstart_, dstart_ + (j - 1) * nbins)
                y = min(dend_, dstart_ + (j + 2) * nbins) + 1
                stime_extend = btime[x:y]
                sflux_extend = bflux[x:y]
                sfluxerr_extend = bfluxerr[x:y]

                w = dstart_ + j * nbins
                z = min(dend_, dstart_ + (j + 1) * nbins) + 1

                ndx = np.where(np.isfinite(bflux[w:z]))[0]

                if len(ndx) <= detrend_order + 1 and detrend_order != 0:
                    dflux[w:z] = np.nan
                    dfluxerr[w:z] = np.nan
                    continue

                ndx = np.where(np.isfinite(sflux_extend))[0]

                m = np.nanmean(btime[w:z])
                c = polyfit(stime_extend[ndx] - m, sflux_extend[ndx],
                    sfluxerr_extend[ndx], detrend_order)

                trend = poly.polyval(btime[w:z] - m, c)

                dflux[w:z] = bflux[w:z] / trend
                dflux[w:z] -= 1.
                dfluxerr[w:z] = bfluxerr[w:z] / trend

    time += t
    btime += t

    return btime, dflux, dfluxerr, bsamples, segstart, segend


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
@cython.embedsignature(True)
def __bls_pulse_binned(np.ndarray[double, ndim=1, mode='c'] time,
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr,
np.ndarray[double, ndim=1, mode='c'] samples, double segsize, double mindur, double maxdur,
int direction, np.ndarray[double, ndim=1, mode='c'] srsq,
np.ndarray[double, ndim=1, mode='c'] duration, np.ndarray[double, ndim=1, mode='c'] depth,
np.ndarray[double, ndim=1, mode='c'] midtime):
    cdef int nbins, n, nbins_min_dur, nbins_max_dur
    cdef double c

    # These arrays will contain all of the final results. They are written inside the external
    # function.
    nbins = time.shape[0]

    nbins_min_dur = max(np.floor(mindur / segsize * nbins), 1)
    nbins_max_dur = np.ceil(maxdur / segsize * nbins)

    # Initialize the preallocated input arrays.
    srsq[:] = 0.
    duration[:] = np.nan
    depth[:] =  np.nan
    midtime[:] = np.nan

    # the total number of points that were binned
    n = np.sum(samples)

    do_bls_pulse_segment(&time[0], &flux[0], &fluxerr[0], &samples[0], nbins, n,
        nbins_min_dur, nbins_max_dur, direction, &srsq[0], &duration[0], &depth[0],
        &midtime[0])


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
@cython.embedsignature(True)
def __bls_pulse_binned_compound(np.ndarray[double, ndim=1, mode='c'] time,
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr,
np.ndarray[double, ndim=1, mode='c'] samples, double segsize, double mindur, double maxdur,
np.ndarray[double, ndim=1, mode='c'] srsq_dip, np.ndarray[double, ndim=1, mode='c'] duration_dip,
np.ndarray[double, ndim=1, mode='c'] depth_dip, np.ndarray[double, ndim=1, mode='c'] midtime_dip,
np.ndarray[double, ndim=1, mode='c'] srsq_blip, np.ndarray[double, ndim=1, mode='c'] duration_blip,
np.ndarray[double, ndim=1, mode='c'] depth_blip, np.ndarray[double, ndim=1, mode='c'] midtime_blip):
    cdef int nbins, n, nbins_min_dur, nbins_max_dur
    cdef double c

    # These arrays will contain all of the final results. They are written inside the external
    # function.
    nbins = time.shape[0]

    nbins_min_dur = max(np.floor(mindur / segsize * nbins), 1)
    nbins_max_dur = np.ceil(maxdur / segsize * nbins)

    # Initialize the preallocated input arrays.
    srsq_dip[:] = 0.
    duration_dip[:] = np.nan
    depth_dip[:] =  np.nan
    midtime_dip[:] = np.nan
    srsq_blip[:] = 0.
    duration_blip[:] = np.nan
    depth_dip[:] =  np.nan
    midtime_dip[:] = np.nan

    # the total number of points that were binned
    n = np.sum(samples)

    do_bls_pulse_segment_compound(&time[0], &flux[0], &fluxerr[0], &samples[0], nbins, n,
        nbins_min_dur, nbins_max_dur, &srsq_dip[0], &duration_dip[0], &depth_dip[0],
        &midtime_dip[0], &srsq_blip[0], &duration_blip[0], &depth_blip[0],
        &midtime_blip[0])

