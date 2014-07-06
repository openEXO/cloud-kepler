# -*- coding: utf-8 -*-

import numpy as np
import detrend.polyfit as polyfit
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
    double *sfluxerr, double *samples)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
def bls_pulse(np.ndarray[double, ndim=1, mode='c'] time,
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr,
int nbins, double segsize, double mindur, double maxdur, int detrend_order=3, direction=0):
    cdef double t
    cdef int i, nsamples, nsegments, save
    cdef np.ndarray[double, ndim=1, mode='c'] stime, sflux, sfluxerr, samples
    cdef np.ndarray[double, ndim=2, mode='c'] srsq, depth, duration, midtime
    cdef np.ndarray[double, ndim=2, mode='c'] srsq_dip, depth_dip, duration_dip, midtime_dip
    cdef np.ndarray[double, ndim=2, mode='c'] srsq_blip, depth_blip, duration_blip, midtime_blip

    # Prepare the lightcurve so that it meets our assumptions.
    t = np.nanmin(time)
    time -= t

    nsamples = np.size(time)
    nsegments = np.floor(np.nanmax(time) / segsize) + 1
    save = 0

    # This memory is only allocated once and will be reused.
    stime = np.empty((nbins,), dtype='float64')
    sflux = np.empty((nbins,), dtype='float64')
    sfluxerr = np.empty((nbins,), dtype='float64')
    samples = np.empty((nbins,), dtype='float64')

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
        # Initialize these to zero for each new segment.
        stime[:] = 0.
        sflux[:] = 0.
        sfluxerr[:] = 0.
        samples[:] = 0.

        # Get the binned data.
        save = __get_binned_segment(time, flux, fluxerr, nbins, segsize, nsamples, i,
            save, stime, sflux, sfluxerr, samples)

        # Perform sigma clipping and polynomial detrending.
        ndx = np.where(np.isfinite(sflux))[0]
        
        if len(ndx) <= detrend_order + 1 and detrend_order != 0:
            # There aren't enough points to do any detrending; go on to the
            # next segment.
            if direction == 2:
                srsq_dip[i,:] = 0.
                depth_dip[i,:] = np.nan
                duration_dip[i,:] = np.nan
                midtime_dip[i,:] = np.nan
                srsq_blip[i,:] = 0.
                depth_blip[i,:] = np.nan
                duration_blip[i,:] = np.nan
                midtime_blip[i,:] = np.nan
            else:
                srsq[i,:] = 0.
                depth[i,:] = np.nan
                duration[i,:] = np.nan
                midtime[i,:] = np.nan

            continue

        if detrend_order != 0:
            coeffs = polyfit.polyfit(stime[ndx], sflux[ndx], sfluxerr[ndx], detrend_order)
            sflux /= poly.polyval(stime, coeffs)
            sflux -= 1.
            
        # Call the algorithm.
        if direction == 2:
            __bls_pulse_binned_compound(stime, sflux, sfluxerr, samples, segsize, mindur,
                maxdur, srsq_dip[i,:], duration_dip[i,:], depth_dip[i,:], midtime_dip[i,:],
                srsq_blip[i,:], duration_blip[i,:], depth_blip[i,:], midtime_blip[i,:])
        else:
            __bls_pulse_binned(stime, sflux, sfluxerr, samples, segsize, mindur, maxdur, 
                direction, srsq[i,:], duration[i,:], depth[i,:], midtime[i,:])

    # Fix the time offset (subtracted off earlier).
    time += t

    if direction == 2:
        midtime_dip += t
        midtime_blip += t
        
        # Maximize over the bin axis.
        ndx1 = np.argmax(srsq_dip, axis=1)
        ind1 = np.indices(ndx1.shape)
        ndx2 = np.argmax(srsq_blip, axis=1)
        ind2 = np.indices(ndx2.shape)

        return dict(srsq_dip=srsq_dip[ind1,ndx1].ravel(), 
            duration_dip=duration_dip[ind1,ndx1].ravel(), depth_dip=depth_dip[ind1,ndx1].ravel(),
            midtime_dip=midtime_dip[ind1,ndx1].ravel(), srsq_blip=srsq_blip[ind2,ndx2].ravel(),
            duration_blip=duration_blip[ind2,ndx2].ravel(), 
            depth_blip=depth_blip[ind2,ndx2].ravel(), midtime_blip=midtime_blip[ind2,ndx2].ravel())
    else:
        midtime += t
        
        # Maximize over the bin axis.
        ndx = np.argmax(srsq, axis=1)
        ind = np.indices(ndx.shape)
    
        return dict(srsq=srsq[ind,ndx].ravel(), duration=duration[ind,ndx].ravel(), 
            depth=depth[ind,ndx].ravel(), midtime=midtime[ind,ndx].ravel())


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
def __get_binned_segment(np.ndarray[double, ndim=1, mode='c'] time, 
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr,
int nbins, double segsize, int nsamples, int n, int ndx, 
np.ndarray[double, ndim=1, mode='c'] stime, np.ndarray[double, ndim=1, mode='c'] sflux,
np.ndarray[double, ndim=1, mode='c'] sfluxerr, np.ndarray[double, ndim=1, mode='c'] samples):
    do_bin_segment(&time[0], &flux[0], &fluxerr[0], nbins, segsize, nsamples, n, &ndx, 
        &stime[0], &sflux[0], &sfluxerr[0], &samples[0])
    return ndx


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
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

