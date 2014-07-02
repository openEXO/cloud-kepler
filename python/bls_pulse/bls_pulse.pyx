# -*- coding: utf-8 -*-

import numpy as np
from numpy.polynomial import polynomial as poly
cimport numpy as np
cimport cython


cdef extern int do_bls_pulse_segment(double *time, double *flux, double *fluxerr, double *samples,
    int nbins, int n, int nbins_min_dur, int nbins_max_dur, double *srsq, double *duration, 
    double *depth, double *midtime)

cdef extern int do_bin_segment(double *time, double *flux, double *fluxerr, int nbins,
    double segsize, int nsamples, int n, int *ndx, double *stime, double *sflux,
    double *sfluxerr, double *samples)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
def bls_pulse_main(np.ndarray[double, ndim=1, mode='c'] time,
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr,
int nbins, double segsize, double mindur, double maxdur, int detrend_order=3):
    '''

    '''
    cdef int i, nsamples, nsegments, save
    cdef np.ndarray[double, ndim=1, mode='c'] stime, sflux, sfluxerr, samples
    cdef np.ndarray[double, ndim=2, mode='c'] srsq, depth, duration, midtime

    # Prepare the lightcurve so that it meets our assumptions.
    __prepare_lightcurve(time, flux, fluxerr)

    nsamples = np.size(time)
    nsegments = np.floor(np.nanmax(time) / segsize) + 1
    save = 0

    # This memory is only allocated once and will be reused.
    stime = np.empty((nbins,), dtype='float64')
    sflux = np.empty((nbins,), dtype='float64')
    sfluxerr = np.empty((nbins,), dtype='float64')
    samples = np.empty((nbins,), dtype='float64')

    # These arrays will contain all output data.
    srsq = np.empty((nsegments,nbins), dtype='float64')
    depth = np.empty((nsegments,nbins), dtype='float64')
    duration = np.empty((nsegments,nbins), dtype='float64')
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
        
        if len(ndx) <= detrend_order + 1 and detrend_order != -1:
            # There aren't enough points to do any detrending; go on to the
            # next segment.
            srsq[i,:] = 0.
            depth[i,:] = np.nan
            duration[i,:] = np.nan
            midtime[i,:] = np.nan
            continue

        if detrend_order != -1:
            coeffs = __lsqclip_detrend(stime[ndx], sflux[ndx], sfluxerr[ndx], detrend_order)
            sflux /= poly.polyval(stime, coeffs)

        # Call the algorithm.
        __bls_pulse_binned(stime, sflux, sfluxerr, samples, segsize, mindur, maxdur, 
            srsq[i,:], duration[i,:], depth[i,:], midtime[i,:])

    return (srsq, duration, depth, midtime)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
def __prepare_lightcurve(np.ndarray[double, ndim=1, mode='c'] time,
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr):
    '''
    Any assumptions about the lightcurve should be resolved in this function.
    '''
    # TODO: Sort by time if it isn't already?
    
    # The phase-binning assumes a zero-based time index.
    time -= time[0]


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
def __lsqclip_detrend(np.ndarray[double, ndim=1, mode='c'] time, 
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr, 
int order, double threshold=3., int niter=3):
    '''

    '''
    cdef int i
    cdef double sigma
    cdef np.ndarray[long, ndim=1, mode='c'] ndx
    cdef np.ndarray[double, ndim=1, mode='c'] x, y, yerr, coeffs, resid

    x = time.copy()
    y = flux.copy()
    yerr = fluxerr.copy()
    i = 0
    
    while i < niter and len(x) > order + 1:
        # Fit the current data or residuals with a polynomial.
        coeffs = poly.polyfit(x, y, order, w=yerr)
        resid = y - poly.polyval(x, coeffs)

        # Calculate the root-mean-square statistic for the fit.
        sigma = np.sqrt(np.sum(resid**2.) / len(x))

        # Perform the sigma clipping.
        ndx = np.where(np.absolute(resid) < threshold * sigma)[0]
        x = x[ndx]
        y = y[ndx]
        yerr = yerr[ndx]
        
        # Increase the iteration counter.
        i += 1

    return coeffs


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
def __get_binned_segment(np.ndarray[double, ndim=1, mode='c'] time, 
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr,
int nbins, double segsize, int nsamples, int n, int ndx, 
np.ndarray[double, ndim=1, mode='c'] stime, np.ndarray[double, ndim=1, mode='c'] sflux,
np.ndarray[double, ndim=1, mode='c'] sfluxerr, np.ndarray[double, ndim=1, mode='c'] samples):
    '''
 
    '''
    do_bin_segment(&time[0], &flux[0], &fluxerr[0], nbins, segsize, nsamples, n, &ndx, 
        &stime[0], &sflux[0], &sfluxerr[0], &samples[0])

    return ndx


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
def __bls_pulse_binned(np.ndarray[double, ndim=1, mode='c'] time, 
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr,
np.ndarray[double, ndim=1, mode='c'] samples, double segsize, double mindur, double maxdur,
np.ndarray[double, ndim=1, mode='c'] srsq, np.ndarray[double, ndim=1, mode='c'] duration,
np.ndarray[double, ndim=1, mode='c'] depth, np.ndarray[double, ndim=1, mode='c'] midtime):
    '''
    Takes binned arrays containing the time, flux, flux error, and sample counts, 
    assuming that flux is already binned, detrended, and normalized to 1. Calls an 
    external C function to perform BLS algorithm on each lightcurve segment.
    '''
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

    # The BLS pulse algorithm described in Kovacs, Zucker, & Mazeh (2002) assumes
    # that the signal has zero arithmetic mean. We correct for that here and then
    # add the correction back to the depths at the end.
    c = np.nanmean(flux)
    flux -= c

    # the total number of points that were binned
    n = np.sum(samples)

    do_bls_pulse_segment(&time[0], &flux[0], &fluxerr[0], &samples[0], nbins, n, 
        nbins_min_dur, nbins_max_dur, &srsq[0], &duration[0], &depth[0], &midtime[0])

    # Undo the flux correction.
    flux += c
    depth += c

