# -*- coding: utf-8 -*-

import numpy as np
from numpy.polynomial import polynomial as poly
cimport numpy as np
cimport cython


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.profile(True)
def polyfit(np.ndarray[double, ndim=1, mode='c'] time,
np.ndarray[double, ndim=1, mode='c'] flux, np.ndarray[double, ndim=1, mode='c'] fluxerr,
int order, double threshold=3., int niter=3):
    '''
    Fits a polynomial to data and removes values by sigma clipping, iterating the
    process as desired.
    
    :param time: Array of times
    :type time: numpy.ndarray
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

        # Calcualte the root-mean-square statistic for the fit.
        sigma = np.sqrt(np.sum(resid**2.) / len(x))

        # Perform the sigma clipping.
        ndx = np.where(np.absolute(resid) < threshold * sigma)[0]
        x = x[ndx]
        y = y[ndx]
        yerr = yerr[ndx]

        # Increase the iteration counter.
        i += 1

    return coeffs

