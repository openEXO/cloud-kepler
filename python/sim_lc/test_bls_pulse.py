############################################################################################
## Place import commands and logging options.
############################################################################################
import logging
import random
import math
import base64
import simplejson
from zlib import compress
import cStringIO
import bls_vec_simulator
import bls_pulse

import numpy
import matplotlib.pyplot as matplot
import matplotlib.transforms

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
############################################################################################


############################################################################################
## This is the main routine.
############################################################################################
def main():

    ## Generate repeatable, random tranist parameters selected from a uniform distribution for testing purposes.
    
    ## This is the value of 1 minute in days (at least roughly).
    minute_in_days = 1. / (60. * 24.)

    ## --- The following parameters are for the bls_pulse input ---
    ## What do you want to use for a segment size in the bls_pulse algorithm?
    segment_size = 10
    min_duration = 0.0416667
    max_duration = 2.0
    n_bins_blspulse = 1000
    ## ------------------------------------------------------------

    ## How many total lightcurves to simulate?
    n_lcs = 10

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
    
    ## Create random distribution of periods, depths, and durations.
    starid_list = [str(x+1).zfill(2) for x in range(n_lcs)]
    period_list = [random.uniform(per_range[0], per_range[1]) for x in range(n_lcs)]
    depth_list = [random.uniform(depth_range[0], depth_range[1]) for x in range(n_lcs)]
    duration_list = [random.uniform(duration_range[0], duration_range[1]) for x in range(n_lcs)]
    phase_list = [random.uniform(phase_range[0], phase_range[1]) for x in range(n_lcs)]

    ## Convert the duration (in hours) into transit duration ratios for use in "simulate_box_lightcurve".
    ## ratio = duration (hours) / 24. * period (days)
    duration_ratio_list = [x/(24.*y) for x,y in zip(duration_list, period_list)]

    ## Andrea Zonca's "simulate_box_lightcurve" takes in the following parameters:
    ##  period (days)
    ##  transit duration (as a ratio of the transit duration to the orbital period)
    ##  transit depth (in normalized units)
    ##  phase shift (we will use 0.0 for now for simplicity)
    ##  signal-to-noise (ratio of transit depth to standard deviation of the white noise)
    ##  n_samples (the number of fixed time samples during the time span)
    ##  time_span (the total time baseline of the simulated lightcurve, in days)

    ## Create the simulated lightcurves.
    for i, p, d, dr, ph in zip(starid_list, period_list, depth_list, duration_ratio_list, phase_list):
        this_lc = bls_vec_simulator.bls_vec_simulator(p, dr, d, ph, signal_to_noise, n_samples, baseline)

        ## Create a list of lists (a list of [time,flux,fluxerr]) to encode and pass onto bls_pulse.
        this_lc_listoflists = [[x,y,z] for x,y,z in zip(this_lc['lc'].index,this_lc['lc'].flux,this_lc['lc'].flux_error)]

        ## Create a lightcurve string object as expected by bls_pulse.
        lc_string = "\t".join( ['TestStar_'+i, '0', base64.b64encode(compress(simplejson.dumps(this_lc_listoflists))) ] )
        lc_string = cStringIO.StringIO(lc_string)

        ## Run the lightcurve through bls_pulse_vec.
        these_srs = bls_pulse.main(segment_size, lc_string, min_duration, max_duration, n_bins_blspulse, -1, "normal")
##        print len(these_srs)
        exit()
        



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()
############################################################################################
