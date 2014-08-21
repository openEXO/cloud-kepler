#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import numpy as np
from simulate import simulate_compound_signal
from bls_pulse_cython import bls_pulse as bls_pulse_cython, bin_and_detrend
from argparse import ArgumentParser
from utils import boxcar


def is_straddling(tmid, tdur, segsize, time):
    '''
    Returns true if, given a time baseline, a segment break occurs inside a
    transit.

    Inputs:
      tmid -- the midtransit time
      tdur -- the duration of the transit
      segsize -- the length of a segment
      lc -- the lightcurve time baseline
    '''
    # The segment break may fall before or after midtransit; calculate those
    # times.
    n = np.floor((tmid - np.amin(time)) / segsize)
    before = segsize * float(n)
    after = segsize * float(n + 1)

    # Is the segment break within half a duration of midtransit?
    if before > tmid - tdur / 2. or after < tmid + tdur / 2.:
        return True
    else:
        return False


def main(err_on_fail=True, allow_straddling=True, ofile=None):
    if ofile is not None:
        ofile.write('#\tMeas. mid.\tAct. mid.\tMeas. dpth.\tAct. dpth.\tMeas. '
            'dur.\tAct. dur\n')

    # Define absolute/relative tolerances.
    midtime_atol = 0.1
    duration_rtol = 0.1
    depth_rtol = 0.1

    # Other parameters.
    minutes_per_day = 24. * 60.
    sigma, baseline = (1.e-5, 100.)
    nsamples = np.ceil(baseline * minutes_per_day)
    segsize, mindur, maxdur, nbins = (2., 0.05, 0.5, 1000)

    # To make it deterministic, seed the PRNG.
    np.random.seed(4)

    # Simulate the lightcurve.
    time, flux, fluxerr, duration, depth, midtime = \
        simulate_compound_signal(baseline, nsamples, sigma, segsize, mindur,
            maxdur)

    dtime, dflux, dfluxerr, dsamples, segstart, segend = \
        bin_and_detrend(time, flux, fluxerr, nbins, segsize, detrend_order=0)

    out = bls_pulse_cython(dtime, dflux, dfluxerr, dsamples, nbins, segsize,
        mindur, maxdur, direction=2)

    bls_du_dip = out['duration_dip']
    bls_dp_dip = out['depth_dip']
    bls_mid_dip = out['midtime_dip']
    bls_du_blip = out['duration_blip']
    bls_dp_blip = out['depth_blip']
    bls_mid_blip = out['midtime_blip']

    bls_du = np.concatenate((bls_du_dip, bls_du_blip))
    bls_dp = np.concatenate((bls_dp_dip, bls_dp_blip))
    bls_mid = np.concatenate((bls_mid_dip, bls_mid_blip))

    for j in xrange(len(midtime)):
        ndx = np.nanargmin(np.absolute(midtime[j] - bls_mid))

        if ofile:
            ofile.write('%d\t%f\t%f\t%f\t%f\t%f\t%f\n' % (j, bls_mid[ndx],
                midtime[j], bls_dp[ndx], depth[j], bls_du[ndx], duration[j]))

        if is_straddling(midtime[j], duration[j], segsize, time):
            print 'Test segment %02d.....PASS (straddling)' % j
            continue

        try:
            diff_midtime = np.absolute(midtime[j] - bls_mid[ndx])
            diff_depth = np.absolute(depth[j] - bls_dp[ndx])
            diff_duration = np.absolute(duration[j] - bls_du[ndx])

            errstring = 'Test segment %02d.....FAIL\n' % j

            if diff_midtime > midtime_atol:
                errstring += 'MIDTIME: Expected ' + str(midtime[j]) + \
                    ', measured ' + str(bls_mid[ndx]) + ', diff. ' + \
                    str(diff_midtime) + ', allowed diff. ' + str(midtime_atol)
                print errstring
                raise RuntimeError
            #elif abs(diff_depth / depth[j]) > depth_rtol:
            #    errstring += 'DEPTH: Expected ' + str(depth[j]) + \
            #        ', measured ' + str(bls_dp[ndx]) + ', rel. diff. ' + \
            #        str(diff_depth / depth[j] * 100) + \
            #        '%, allowed rel. diff. ' + str(depth_rtol * 100) + '%'
            #    print errstring
            #    raise RuntimeError
            elif abs(diff_duration / duration[j]) > duration_rtol:
                errstring += 'DURATION: Expected ' + str(duration[j]) + \
                    ', measured ' + str(bls_du[ndx]) + ', rel. diff. ' + \
                    str(diff_duration / duration[j] * 100) + \
                    '%, allowed diff. ' + str(duration_rtol * 100) + '%'
                print errstring
                raise RuntimeError
            else:
                # All values within relative or absolute tolerances.
                print 'Test segment %02d.....PASS' % j
        except RuntimeError:
            if err_on_fail:
                sys.exit(1)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-e', help='Throw an error if a test fails?', default=1,
        dest='err', type=int)
    parser.add_argument('-s', help='Allow straddling transits to pass?',
        default=1, dest='straddling', type=int)
    parser.add_argument('-o', help='Specify an output file', default=None,
        dest='ofile', type=str)
    args = parser.parse_args()

    print 'Errors on fail:', bool(args.err)
    print 'Allow straddling to pass:', bool(args.straddling)
    print

    if args.ofile is not None:
        f = open(args.ofile, 'w')
    else:
        f = None

    main(err_on_fail=args.err, allow_straddling=args.straddling, ofile=f)

    if f is not None:
        f.close()
