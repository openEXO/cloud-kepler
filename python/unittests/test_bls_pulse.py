#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import numpy as np
from simulate import simulate_box_lightcurve
from bls_pulse import bls_pulse_main


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


if __name__ == '__main__':
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

    period_list = np.random.uniform(2., 30., size=n)                # days
    duration_list = np.random.uniform(1. / 24., 5. / 24., size=n)   # days
    depth_list = np.random.uniform(0.01, 0.5, size=n)
    phase_list = np.random.uniform(0., 1., size=n)

    for i, p, du, dp, ph in zip(np.arange(n), period_list, duration_list, depth_list,
    phase_list):
        # Print a status update message.
        print 'TEST_BLS_PULSE: Test case', i + 1, 'of', n, '...'

        # Simulate the lightcurve.
        time, flux, fluxerr, duration, depth, midtime = simulate_box_lightcurve(p, du,
            dp, ph, signal_to_noise, nsamples, baseline)

        srsq, bls_du, bls_dp, bls_mid = bls_pulse_main(time, flux, fluxerr, nbins,
            segsize, mindur, maxdur, detrend_order=-1)

        # Calculate the segment numbers to check.
        ndx = np.floor(midtime / segsize).astype('int32')

        for i, j in zip(range(len(ndx)), ndx):
            # These indices now give (i,j) = (event,segment).
            ndx = np.argmax(srsq[j,:])

            if is_straddling(midtime[i], duration[i], segsize, time):
                print '    Transit %02d.....PASS (straddling)' % i
            else:
                diff_midtime = np.absolute(midtime[i] - bls_mid[j,ndx])
                diff_depth = np.absolute(depth[i] - bls_dp[j,ndx])
                diff_duration = np.absolute(duration[i] - bls_du[j,ndx])

                errstring = '    Transit %02d.....FAIL\n' % i

                if diff_midtime > midtime_atol:
                    errstring += 'MIDTIME: Expected ' + str(midtime[i]) + ', measured ' + \
                        str(bls_mid[j,ndx]) + ', diff. ' + str(diff_midtime) + \
                        ', allowed diff. ' + str(midtime_atol)
                    print errstring
                    sys.exit(1)
                elif diff_depth / depth[i] > depth_rtol:
                    errstring += 'DEPTH: Expected ' + str(depth[i]) + ', measured ' + \
                        str(bls_dp[j,ndx]) + ', rel. diff. ' + \
                        str(diff_depth / depth[i] * 100) + '%, allowed rel. diff. ' + \
                        str(depth_rtol * 100) + '%'
                    print errstring
                    sys.exit(1)
                elif diff_duration / duration[i] > duration_rtol:
                    errstring += 'DURATION: Expected ' + str(duration[i]) + ', measured ' + \
                        str(bls_du[j,ndx]) + ', rel. diff. ' + \
                        str(diff_duration / duration[i] * 100) + '%, allowed diff. ' + \
                        str(duration_rtol * 100) + '%'
                    print errstring
                    sys.exit(1)
                else:
                    # All values within relative or absolute tolerances.
                    print '    Transit %02d.....PASS' % i

