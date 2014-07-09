#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import numpy as np
import matplotlib.pyplot as plt
from time import clock
from simulate import simulate_box_lightcurve
from bls_pulse_python import bls_pulse as bls_pulse_python
from bls_pulse_vec import bls_pulse as bls_pulse_vec
from bls_pulse_cython import bls_pulse as bls_pulse_cython

np.seterr(all='ignore')


def main():
    # Number of trials.
    n = 10

    # Other parameters.
    baseline = 90.      # days
    minutes_per_day = 24. * 60.
    signal_to_noise = 10000.
    nsamples = np.ceil(baseline * minutes_per_day)
    segsize, mindur, maxdur, nbins = (2., 0.01, 0.5, 1000)

    # To make it deterministic, seed the PRNG.
    np.random.seed(4)

    period = np.random.uniform(segsize, 30.)            # days
    duration = np.random.uniform(1. / 24., 5. / 24.)    # days
    depth = np.random.uniform(-0.01, -0.5)
    phase = 0.5

    # Create logarithmically spaced numbers of lightcurves.
    num_lightcurves = np.logspace(0., 3., n).astype('int64')

    # Allocate memory to store results.
    cython_times = np.zeros((n,), dtype='float64')

    for i in xrange(n):
        # Print a status update message.
        print 'BENCHMARK: # lightcurves =', num_lightcurves[i], '/', i + 1, 'of', n, '...'

        for j in xrange(num_lightcurves[i]):
            # Simulate the lightcurve.
            time, flux, fluxerr, _, _, _ = simulate_box_lightcurve(period,
                duration, depth, phase, signal_to_noise, nsamples, baseline)

            cython_start = clock()
            out_cython = bls_pulse_cython(time, flux, fluxerr, nbins, segsize, mindur, maxdur,
                detrend_order=0, direction=0)
            cython_end = clock()

            cython_times[i] += cython_end - cython_start

    np.savez('unittests/benchmark2.npz', num_lightcurves=num_lightcurves, cython_times=cython_times)
    __generate_figure()


def __generate_figure(infile='unittests/benchmark2.npz'):
    data = np.load(infile)
    num_lightcurves = data['num_lightcurves']
    cython_times = data['cython_times']

    plt.plot(num_lightcurves, cython_times, color='blue')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Number of lightcurves')
    plt.ylabel('Time (seconds)')
    plt.savefig('unittests/benchmark2.png')


if __name__ == '__main__':
    main()

