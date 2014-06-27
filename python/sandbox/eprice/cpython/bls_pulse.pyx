# -*- coding: utf-8 -*-

import cython
import sys
import numpy as np
cimport numpy as np


cdef extern int do_bls_pulse_segment(double *time, double *flux, double *fluxerr, double *samples,
    int nbins, int n, int nbins_min_dur, int nbins_max_dur, double *srsq, double *duration, 
    double *depth, double *midtime)


def bls_pulse_binned(np.ndarray[double, ndim=2, mode='c'] time, 
np.ndarray[double, ndim=2, mode='c'] flux, np.ndarray[double, ndim=2, mode='c'] fluxerr,
np.ndarray[double, ndim=2, mode='c'] samples, double segsize, double mindur, double maxdur):
    '''
    Takes arrays of shape (segments,bins) containing the time, flux, flux error, and
    sample counts, assuming that flux is already binned, detrended, and normalized to 1. 
    Calls an external C function to perform BLS algorithm on each lightcurve segment.
    '''
    cdef int nsegments, nbins, n, m, nbins_min_dur, nbins_max_dur
    cdef double c
    cdef np.ndarray[double, ndim=2, mode='c'] srsq, duration, depth, midtime

    # These arrays will contain all of the final results. They are written inside the external
    # function.
    nsegments = time.shape[0]
    nbins = time.shape[1]
    srsq = np.empty((nsegments,nbins), dtype='float64')
    duration = np.empty((nsegments,nbins), dtype='float64')
    depth = np.empty((nsegments,nbins), dtype='float64')
    midtime = np.empty((nsegments,nbins), dtype='float64')

    nbins_min_dur = max(np.floor(mindur / segsize * nbins), 1)
    nbins_max_dur = np.ceil(maxdur / segsize * nbins)
    
    for i in xrange(nsegments):
        # The BLS pulse algorithm described in Kovacs, Zucker, & Mazeh (2002) assumes
        # that the signal has zero arithmetic mean. We correct for that here and then
        # add the correction back to the depths at the end.
        c = np.mean(flux[i,:])
        flux -= c

        # the total number of points that were binned
        n = np.sum(samples[i,:])

        do_bls_pulse_segment(&time[i,0], &flux[i,0], &fluxerr[i,0], &samples[i,0], nbins, n, 
            nbins_min_dur, nbins_max_dur, &srsq[i,0], &duration[i,0], &depth[i,0], &midtime[i,0])

        # Undo the flux correction.
        flux += c
        
        # Convert `depth` from a level to a depth relative to 1, taking the flux correction
        # into account.
        depth[i,:] = 1. - (depth[i,:] + c)

    return (srsq, duration, depth, midtime)

