#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import numpy as np
from simulate import simulate_box_lightcurve
from bls_pulse_python import bls_pulse as bls_pulse_python
from bls_pulse_vec import bls_pulse as bls_pulse_vec
from bls_pulse_cython import bls_pulse as bls_pulse_cython
from argparse import ArgumentParser


def is_straddling(tmid, tdur, segsize, time):
    '''
    Returns true if, given a time baseline, a segment break occurs inside a transit.

    Inputs:
      tmid -- the midtransit time
      tdur -- the duration of the transit
      segsize -- the length of a segment
      lc -- the lightcurve time baseline
    '''
    # The segment break may fall before or after midtransit; calculate those times.
    n = np.floor((tmid - np.amin(time)) / segsize)
    before = segsize * float(n)
    after = segsize * float(n + 1)

    # Is the segment break within half a duration of midtransit?
    if before > tmid - tdur / 2. or after < tmid + tdur / 2.:
        return True
    else:
        return False


def main(err_on_fail=True, allow_straddling=True, ofile=None, mode='python'):
    if ofile is not None:
        ofile.write('#\tMeas. mid.\tAct. mid.\tMeas. dpth.\tAct. dpth.\tMeas. dur.\tAct. dur\n')

    # Define absolute/relative tolerances.
    midtime_atol = 0.1
    duration_rtol = 0.1
    depth_rtol = 0.1

    # How many lightcurves to simulate.
    n = 10

    # Other parameters.
    minutes_per_day = 24. * 60.
    signal_to_noise, baseline = (10000., 90.)
    nsamples = np.ceil(baseline * minutes_per_day)
    segsize, mindur, maxdur, nbins = (2., 0.01, 0.5, 1000)

    # To make it deterministic, seed the PRNG.
    np.random.seed(4)

    period_list = np.random.uniform(segsize, 30., size=n)           # days
    duration_list = np.random.uniform(1. / 24., 5. / 24., size=n)   # days
    depth_list = np.random.uniform(-0.01, -0.5, size=n)
    phase_list = np.random.uniform(0., 1., size=n)

    for i, p, du, dp, ph in zip(np.arange(n), period_list, duration_list, depth_list,
    phase_list):
        # Print a status update message.
        print 'TEST_BLS_PULSE: Test case', i + 1, 'of', n, '...'

        # Simulate the lightcurve.
        time, flux, fluxerr, duration, depth, midtime = simulate_box_lightcurve(p, du,
            dp, ph, signal_to_noise, nsamples, baseline)

        if mode == 'python':
            out = bls_pulse_python(time, flux, fluxerr, nbins, segsize, mindur, maxdur,
                detrend_order=0, direction=0)
        elif mode == 'vec':
            out = bls_pulse_vec(time, flux, fluxerr, nbins, segsize, mindur, maxdur,
                detrend_order=0, direction=0)
        elif mode == 'cython':
            out = bls_pulse_cython(time, flux, fluxerr, nbins, segsize, mindur, maxdur,
                detrend_order=0, direction=0)
        else:
            raise ValueError('Invalid test mode: %s' % mode)

        bls_du = out['duration'].ravel()
        bls_dp = out['depth'].ravel()
        bls_mid = out['midtime'].ravel()

        for j in xrange(len(midtime)):
            ndx = np.nanargmin(np.absolute(midtime[j] - bls_mid))

            if ofile:
                ofile.write('%d\t%f\t%f\t%f\t%f\t%f\t%f\n' % (j, bls_mid[ndx], midtime[j],
                    bls_dp[ndx], depth[j], bls_du[ndx], duration[j]))

            if is_straddling(midtime[j], duration[j], segsize, time):
                print '    Transit %02d.....PASS (straddling)' % j
                continue

            try:
                diff_midtime = np.absolute(midtime[j] - bls_mid[ndx])
                diff_depth = np.absolute(depth[j] - bls_dp[ndx])
                diff_duration = np.absolute(duration[j] - bls_du[ndx])

                errstring = '    Transit %02d.....FAIL\n' % j

                if diff_midtime > midtime_atol:
                    errstring += 'MIDTIME: Expected ' + str(midtime[j]) + ', measured ' + \
                        str(bls_mid[ndx]) + ', diff. ' + str(diff_midtime) + \
                        ', allowed diff. ' + str(midtime_atol)
                    print errstring
                    raise RuntimeError
                elif diff_depth / depth[j] > depth_rtol:
                    errstring += 'DEPTH: Expected ' + str(depth[j]) + ', measured ' + \
                        str(bls_dp[ndx]) + ', rel. diff. ' + \
                        str(diff_depth / depth[j] * 100) + '%, allowed rel. diff. ' + \
                        str(depth_rtol * 100) + '%'
                    print errstring
                    raise RuntimeError
                elif diff_duration / duration[j] > duration_rtol:
                    errstring += 'DURATION: Expected ' + str(duration[j]) + ', measured ' + \
                        str(bls_du[ndx]) + ', rel. diff. ' + \
                        str(diff_duration / duration[j] * 100) + '%, allowed diff. ' + \
                        str(duration_rtol * 100) + '%'
                    print errstring
                    raise RuntimeError
                else:
                    # All values within relative or absolute tolerances.
                    print '    Transit %02d.....PASS' % j
            except RuntimeError:
                if err_on_fail:
                    sys.exit(1)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-e', help='Throw an error if a test fails?', default=1,
        dest='err', type=int)
    parser.add_argument('-s', help='Allow straddling transits to pass?', default=1,
        dest='straddling', type=int)
    parser.add_argument('-o', help='Specify an output file', default=None,
        dest='ofile', type=str)
    parser.add_argument('-m', '--mode', help='Algorithm to test', default='python',
        dest='mode', type=str)
    args = parser.parse_args()

    print 'Test mode:', args.mode
    print 'Errors on fail:', bool(args.err)
    print 'Allow straddling to pass:', bool(args.straddling)
    print

    if args.ofile is not None:
        f = open(args.ofile, 'w')
    else:
        f = None

    main(err_on_fail=args.err, allow_straddling=args.straddling, ofile=f, mode=args.mode)

    if f is not None:
        f.close()
