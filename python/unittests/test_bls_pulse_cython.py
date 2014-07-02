#!/usr/bin/env python

############################################################################################
## Place import commands and logging options.
############################################################################################
import sys
import random
import math
import simulate.bls_vec_simulator as bls_vec_simulator
from bls_pulse import bls_pulse_main
from argparse import ArgumentParser

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
############################################################################################


def is_straddling(tmid, tdur, segsize, lc):
    '''
    Returns true if, given a time baseline, a segment break occurs inside a transit.

    Inputs:
      tmid -- the midtransit time
      tdur -- the duration of the transit
      segsize -- the length of a segment
      lc -- the lightcurve data (for extracting the time); this function assumes that the
        first segment occurs at the minimum time
    '''
    # Extract the time from the DataFrame.
    time = np.array(lc.index.values, dtype='float64')

    # The segment break may fall before or after midtransit; calculate those times.
    n = np.floor((tmid - np.amin(time)) / segsize)
    before = segsize * float(n)
    after = segsize * float(n + 1)

    # Is the segment break within half a duration of midtransit?
    if before > tmid - tdur / 2. or after < tmid + tdur / 2.:
        return True
    else:
        return False


############################################################################################
## This is the main routine.
############################################################################################
def main(err_on_fail=True, allow_straddling=True, ofile=None):
    ## Generate repeatable, random tranist parameters selected from a uniform distribution for testing purposes.

    if f:
        f.write('#\tMeas. mid.\tAct. mid.\tMeas. dpth.\tAct. dpth.\tMeas. dur.\tAct. dur\n')

    ## This is the value of 1 minute in days (at least roughly).
    minute_in_days = 1. / (60. * 24.)

    ## --- The following parameters are for the bls_pulse input ---
    ## What do you want to use for a segment size in the bls_pulse_vec algorithm?
    segment_size = 2 ## in days.
    min_duration = 0.01 ## in days.
    max_duration = 0.5 ## in days.
    n_bins_blspulse = 1000
    ## ------------------------------------------------------------

    ## How many total lightcurves to simulate?
    n_lcs = 10

    ## Define the precision level that counts as a success.  The mid-transit times, durations, and depths must match the simulated lightcurve's transits to within this precision percentage.
    midtime_precision_threshold = 0.1 ## +/- 0.1 days for now.
    duration_rel_precision_threshold = 0.1 ## +/- 10% (relative precision) allowed for now.
    depth_rel_precision_threshold = 0.1 ## +/- 10% (relative precision) allowed for now.

    ## How long of a baseline do you want to use (in days)?
    baseline = 90.

    ## Determine the number of samples.  We want 1 min. cadence, so the number of samples is the baseline in *minutes* such that each sample is 1 minute in duration.
    n_samples = math.ceil(baseline / minute_in_days)

    ## What signal-to-noise should the lightcurves have (we want these nearly perfect for unit testing, so use a high value).
    signal_to_noise = 10000.

    ## At what phase should we start the transits?  Let's randomize this too between 0. and 1.
    phase_range = (0.0,1.0)

    ## What is the period range?  These are in days.
    per_range = (0.5, 30.)

    ## What is the depth range?  These are in percentages.
    depth_range = (0.01, 0.5)

    ## What is the transit duration range?  These are in hours.
    duration_range = (1., 5.)

    ## Start the random seed variable so the random sampling is repeatable.
    random.seed(4)
    np.random.seed(4)

    ## Create random distribution of periods, depths, and durations.
    starid_list = [str(x+1).zfill(2) for x in range(n_lcs)]
    period_list = [random.uniform(per_range[0], per_range[1]) for x in range(n_lcs)]
    depth_list = [random.uniform(depth_range[0], depth_range[1]) for x in range(n_lcs)]
    duration_list = [random.uniform(duration_range[0], duration_range[1]) for x in range(n_lcs)]
    phase_list = [random.uniform(phase_range[0], phase_range[1]) for x in range(n_lcs)]

    ## Convert the duration (in hours) into transit duration ratios for use in "simulate_box_lightcurve".
    ## ratio = duration (hours) / (24. * period (days))
    duration_ratio_list = [x/(24.*y) for x,y in zip(duration_list, period_list)]

    ## Andrea Zonca's "simulate_box_lightcurve" takes in the following parameters:
    ##  period (days)
    ##  transit duration (as a ratio of the transit duration to the orbital period)
    ##  transit depth (in normalized units)
    ##  phase shift
    ##  signal-to-noise (ratio of transit depth to standard deviation of the white noise)
    ##  n_samples (the number of fixed time samples during the time span)
    ##  time_span (the total time baseline of the simulated lightcurve, in days)

    ## Create the simulated lightcurves.
    for i, p, d, dr, ph in zip(starid_list, period_list, depth_list, duration_ratio_list, phase_list):
        ## Print out status update.
        print "TEST_BLS_PULSE: Test case # " + str(i) + "/" + str(n_lcs) + "..."
        this_lc = bls_vec_simulator.bls_vec_simulator(p, dr, d, ph, signal_to_noise, n_samples, baseline)

        # Re-package the output into the format expected by the Cython implementation.
        time = np.array(this_lc['lc'].index.values, dtype='float64')
        flux = np.array(this_lc['lc'].flux, dtype='float64')
        fluxerr = np.array(this_lc['lc'].flux_error, dtype='float64')

        ## Run the lightcurve through bls_pulse_vec.
        srsq, duration, depth, midtime = bls_pulse_main(time, flux, fluxerr, n_bins_blspulse,
            segment_size, min_duration, max_duration, detrend_order=-1)

        # Re-package the output into the format expected by this module.
        ndx = np.argmax(srsq, axis=1)
        ind = np.indices(ndx.shape)
        durations = duration[ind,ndx][0] * 24.
        depths = depth[ind,ndx][0]
        midtimes = midtime[ind,ndx][0]
        these_srs = pd.Series(dict(durations=durations, depths=depths, midtimes=midtimes))

        ## Compare to see if each of the simulated transits is found by BLS_PULSE.
        for tnum,ttime,tdepth,tduration in zip(range(len(this_lc['transit_times'])), this_lc['transit_times'], this_lc['transit_depths'], this_lc['transit_durations']):
            ## Find the index of the closest segment by comparing the times.
            try:
                closest_index = np.nanargmin(abs(ttime-these_srs["midtimes"].values))
            except ValueError:
                print "*** Warning in TEST_BLS_PULSE: All segments had no events.  Unable to run pass/fail test, defaulting to FAIL.."
                print "   Transit {0: <3d}...FAIL".format(tnum)

                if err_on_fail:
                    sys.exit(1)
            else:
                if ofile:
                    ofile.write('%d\t%f\t%f\t%f\t%f\t%f\t%f\n' % (tnum,
                        these_srs['midtimes'].values[closest_index], ttime,
                        these_srs['depths'].values[closest_index], tdepth,
                        these_srs['durations'].values[closest_index], tduration))

                ## Test pass/fail criteria using the closest segment event.
                if abs(ttime-these_srs["midtimes"].values[closest_index]) <= midtime_precision_threshold and abs((tdepth-these_srs["depths"].values[closest_index])/tdepth) <= depth_rel_precision_threshold and abs((tduration-these_srs["durations"].values[closest_index])/tduration) <= duration_rel_precision_threshold:
                    print "   Transit {0: <3d}.....PASS".format(tnum)
                elif allow_straddling and is_straddling(ttime, tduration / 24., segment_size,
                this_lc['lc']):
                    print "   Transit {0: <3d}.....PASS (straddling)".format(tnum)
                else:
                    err_string_to_add = ""
                    err_string_line2 = ""
                    if abs(ttime-these_srs["midtimes"].values[closest_index]) >= midtime_precision_threshold:
                        err_string_to_add += " (timestamp)"
                        err_string_line2 += "\n\tTIMESTAMP: Expected: " + str(ttime) + " Measured: " + str(these_srs["midtimes"].values[closest_index]) + " Diff: " + str(abs(ttime-these_srs["midtimes"].values[closest_index])) + " Allowed Diff: " + str(midtime_precision_threshold)
                    if abs(tdepth-these_srs["depths"].values[closest_index])/tdepth >= depth_rel_precision_threshold:
                        err_string_to_add += " (depth)"
                        err_string_line2 += "\n\tDEPTH: Expected: " + str(tdepth) + " Measured: " + str(these_srs["depths"].values[closest_index]) + " Rel. Diff: " + str(abs(tdepth-these_srs["depths"].values[closest_index])/tdepth*100.) + "% Allowed Rel. Diff: " + str(depth_rel_precision_threshold*100.)+"%"
                    if abs(tduration-these_srs["durations"].values[closest_index])/tduration >= duration_rel_precision_threshold:
                        err_string_to_add += " (duration)"
                        err_string_line2 += "\n\tDURATION: Expected: " + str(tduration) + " Measured: " + str(these_srs["durations"].values[closest_index]) + " Rel. Diff: " + str(abs(tduration-these_srs["durations"].values[closest_index])/tduration*100.) + "% Allowed Rel. Diff: " + str(duration_rel_precision_threshold*100.)+"%"
                    print "   Transit {0: <3d}...FAIL".format(tnum) + err_string_to_add
                    print err_string_line2

                    if err_on_fail:
                        sys.exit(1)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-e', help='Throw an error if a test fails?', default=1,
        dest='err', type=int)
    parser.add_argument('-s', help='Allow straddling transits to pass?', default=1,
        dest='straddling', type=int)
    parser.add_argument('-o', help='Specify an output file', default=None,
        dest='ofile', type=str)
    args = parser.parse_args()

    print 'Errors on fail:', bool(args.err)
    print 'Allow straddling to pass:', bool(args.straddling)
    print

    if args.ofile:
        f = open(args.ofile, 'w')
    else:
        f = None

    main(err_on_fail=args.err, allow_straddling=args.straddling, ofile=f)

    if f:
        f.close()

############################################################################################
