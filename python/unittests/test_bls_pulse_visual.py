#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from numpy.polynomial import polynomial as poly
from bls_pulse import bls_pulse_main, __lsqclip_detrend, __get_binned_segment
from simulate import bls_vec_simulator
import matplotlib.pyplot as plt


def boxcar(time, duration, depth, midtime):
    flux = np.ones_like(time)
    ndx = np.where((time >= midtime - duration / 2.) & (time < midtime + duration / 2.))
    flux[ndx] = 1. - depth
    return flux


if __name__ == '__main__':
    nbins, segsize, mindur, maxdur = (100, 2., 0.01, 0.5)

    sim = bls_vec_simulator.bls_vec_simulator(signal_to_noise=10.)

    lc = sim['lc']
    time = np.array(lc.index.values, dtype='float64')
    flux = np.array(lc.flux.values, dtype='float64') + 1.
    fluxerr = np.array(lc.flux_error.values, dtype='float64')
    srsq, duration, depth, midtime = bls_pulse_main(time, flux, fluxerr, nbins, segsize,
        mindur, maxdur)

    save = 0

    nsegments = int(np.ceil(np.amax(time) / segsize))
    for i in xrange(nsegments):
        ndx = np.where((time >= segsize * i) & (time < segsize * (i + 1)))
        t = time[ndx]
        f = flux[ndx]
        e = fluxerr[ndx]
        plt.plot(t, f)

        stime = np.zeros((nbins,), dtype='float64')
        sflux = np.zeros((nbins,), dtype='float64')
        sfluxerr = np.zeros((nbins,), dtype='float64')
        samples = np.zeros((nbins,), dtype='float64')
        save = __get_binned_segment(time, flux, fluxerr, nbins, segsize, np.size(time), i,
            save, stime, sflux, sfluxerr, samples)
        coeffs = __lsqclip_detrend(stime, sflux, sfluxerr, 3)
        sflux /= poly.polyval(stime, coeffs)
        plt.scatter(stime, sflux, color='g')

        ndx = np.argmax(srsq[i,:])
        print srsq[i,ndx], duration[i,ndx], depth[i,ndx], midtime[i,ndx]

        tt = np.linspace(np.amin(t), np.amax(t), 1000)
        ff = boxcar(tt, duration[i,ndx], depth[i,ndx], midtime[i,ndx])
        plt.plot(tt, ff)

        plt.xlim(np.amin(t), np.amax(t))
        plt.ylim(np.amin(f), np.amax(f))
        plt.show()

