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
    # Number of baselines to try.
    n = 10

    # Other parameters.
    minutes_per_day = 24. * 60.
    signal_to_noise = 10000.
    segsize, mindur, maxdur, nbins = (2., 0.01, 0.5, 1000)

    # To make it deterministic, seed the PRNG.
    np.random.seed(4)

    duration = np.random.uniform(1. / 24., 5. / 24.)    # days
    depth = np.random.uniform(-0.01, -0.5)
    phase = 0.5

    # Create logarithmically spaced baselines.
    baselines = np.logspace(1., 3., n)

    # Allocate memory to store results.
    python_times = np.empty_like(baselines)
    vec_times = np.empty_like(baselines)
    cython_times = np.empty_like(baselines)

    for i in xrange(n):
        # Print a status update message.
        print 'BENCHMARK: Baseline =', baselines[i], '/', i + 1, 'of', n, '...'

        # Simulate the lightcurve.
        nsamples = np.ceil(baselines[i] * minutes_per_day)
        period = np.random.uniform(segsize, baselines[i])   # days
        time, flux, fluxerr, _, _, _ = simulate_box_lightcurve(period,
            duration, depth, phase, signal_to_noise, nsamples, baselines[i])

        sys.stdout.write('  Running Python test...')
        sys.stdout.flush()
        python_start = clock()
        out_python = bls_pulse_python(time, flux, fluxerr, nbins, segsize, mindur, maxdur,
            detrend_order=0, direction=0)
        python_end = clock()
        sys.stdout.write(' done.\n')
        sys.stdout.flush()

        sys.stdout.write('  Running vectorized test...')
        sys.stdout.flush()
        vec_start = clock()
        out_vec = bls_pulse_vec(time, flux, fluxerr, nbins, segsize, mindur, maxdur,
            detrend_order=0, direction=0)
        vec_end = clock()
        sys.stdout.write(' done.\n')
        sys.stdout.flush()

        sys.stdout.write('  Running Cython test...')
        sys.stdout.flush()
        cython_start = clock()
        out_cython = bls_pulse_cython(time, flux, fluxerr, nbins, segsize, mindur, maxdur,
            detrend_order=0, direction=0)
        cython_end = clock()
        sys.stdout.write(' done.\n')
        sys.stdout.flush()

        python_times[i] = python_end - python_start
        vec_times[i] = vec_end - vec_start
        cython_times[i] = cython_end - cython_start

    np.savez('unittests/benchmark.npz', baselines=baselines, python_times=python_times,
        vec_times=vec_times, cython_times=cython_times)
    __generate_figure()


def __generate_figure(infile='unittests/benchmark.npz'):
    data = np.load(infile)
    baselines = data['baselines']
    python_times = data['python_times']
    vec_times = data['vec_times']
    cython_times = data['cython_times']

    plt.plot(baselines, python_times, color='#bd553c', lw=2., label='Pure Python')
    plt.plot(baselines, vec_times, color='#8ab138', lw=2., label='Vectorized Python')
    plt.plot(baselines, cython_times, color='#2d537b', lw=2., label='Cython')
    plt.legend(loc='best')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Baseline length (days)')
    plt.ylabel('Time (seconds)')
    plt.savefig('unittests/benchmark.png')


if __name__ == '__main__':
    main()

