############################################################################################
## Place import commands and logging options.
############################################################################################
import numpy
import logging
import sys
import math
from random import gauss
from optparse import OptionParser

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
############################################################################################


############################################################################################
## This class defines a generic Exception to use for errors raised in MAKE_LC and is specific to this module.  It simply returns the given value when raising the exception, e.g., raise MAKE_LC("Print this string") -> __main__.MyError: 'Print this string.'
############################################################################################
class MakeLCError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
############################################################################################


############################################################################################
## This function sets up command-line options and arguments through the OptionParser class.
############################################################################################
def setup_input_options(parser):
    ## Should change to operate in units days, currently it's still in data points.
    parser.add_option("-p", "--period", action="store", type="float", dest="period", help="[Required] Period of simulated transit (days).  There is no default value.")
    parser.add_option("-d", "--depth", action="store", type="float", dest="depth", help="[Required] Depth of simulated transit (percentage).  There is no default value.")
    parser.add_option("-w", "--duration", action="store", type="float", dest="duration", help="[Required] Duration of simulated transit (hours).  There is no default value.")
    parser.add_option("-e", "--sigma", action="store", type="float", dest="sigma", help="[Optional] One-sigma uncertainty to use when applying Gaussian error (percentage).  There is no default v")
    parser.add_option("-s", "--shift", action="store", type="float", dest="shift", help="[Optional] Phase shift to apply to simulated transit (days).  There is no default value.")
############################################################################################


############################################################################################
## This function checks input arguments satisfy some minimum requirements.
############################################################################################
def check_input_options(period, depth, duration):
    if period <= 0.0:
        raise MakeLCError("Period must be > 0.")
    if depth < 0.0 or depth > 1.0:
        raise MakeLCError("Transit depth must be 0.0 <= depth <= 1.0.")
    if duration <= 0.0:
        raise MakeLCError("Transit duration must be >= 0.")
############################################################################################


############################################################################################
## This function applies a random Gaussian error to each data point, given a 1-sigma value.
############################################################################################
def add_gauss_uncertainty(flux, sigma):
    pass;
    ## CODING STUB!!
############################################################################################


############################################################################################
## This function applies a random Gaussian error to each data point, given a 1-sigma value.
############################################################################################
def generate_simulated_lc(times, period, depth, duration):
    pass;
    ## CODING STUB!!
############################################################################################


############################################################################################
## This is the main routine.  You can call it from the command-line using the command-line options to specify things like period, depth, and duration, or from a calling function (see drive_make_lc.py).  Note that at the moment I'm not sure how to handle specifying a list of times from the command-line, in that case the default is just to simulate 3 years of constant observations at 1-minute cadence.

## TO-DO LIST

## - Add ability to apply flux errors, phase shifts.
## - How to pass array of times from the command-line, if at all?
## - NOTE: When creating lightcurve, I think we just calculate phases and determine if they fall in or out of eclipse, then apply to the unfolded array of times...
############################################################################################
def make_lc(obs_times=None, period=None, depth=None, duration=None):
    ## This is the value of 1 minute in days (at least roughly).
    minute_in_days = 1. / (60. * 24.)

    ## Define input options.
    parser = OptionParser(usage="%prog -p -d -w [-e] [-s]", version="%prog 1.0")
    setup_input_options(parser)

    ## Parse input options from the command line.
    opts, args = parser.parse_args()
    
    ## There are a few required keywords, so make sure they are defined on input.
    if not opts.period and not period:
        parser.error("No period specified.  Specify with the -p option.")
    if not opts.depth and not depth:
        parser.error("No transit depth specified.  Specify with the -d option.")
    if not opts.duration and not duration:
        parser.error("No transit duration specified.  Specify with the -w option.")

    ## If specified via command-line argument, then input variables are defined from the input options.
    if opts.period:
        period = opts.period
    if opts.depth:
        depth = opts.depth
    if opts.duration:
        duration = opts.duration

    ## Check input arguments are valid and sensible.
    check_input_options(period, depth, duration)

    ## Create the high-cadence (1-minute) lightcurve.  If the list of times is not defined, then this is 3-years sampled at 1-minute cadence starting at JD roughly equal to the start of the Kepler mission.  Otherwise, it spans the start to end of the input time array at 1-minute cadence.
    if not obs_times:
        time_range = 365.
        high_res_obs_times = numpy.linspace(2454953.53889, 2454953.53889+365., math.ceil(time_range/minutes_in_days))
    else:
        min_time = min(obs_times)
        max_time = max(obs_times)
        time_range = max_time - min_time
        high_res_obs_times = numpy.linspace(min_time, max_time, math.ceil(time_range/minute_in_days))
    high_res_lc = generate_simulated_lc(high_res_obs_times, period, depth, duration)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    make_lc()
############################################################################################
