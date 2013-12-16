#!/usr/bin/env python
############################################################################################
## BLS_PULSE algorithm, based on bls_pulse.pro originally written by Peter McCullough.
############################################################################################


############################################################################################
## Place import commands and logging options.
############################################################################################
import numpy
import simplejson
from zlib import decompress, compress
import base64
import logging
import sys
import math
from bls_search import encode_arr

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
############################################################################################


############################################################################################
## This function reads in data from the stream.
############################################################################################
def read_mapper_output(file, separator='\t'):
    for line in file:
        kic, quarters, flux_string = line.rstrip().split(separator)
        flux_array = simplejson.loads((decompress(base64.b64decode(flux_string))))
        yield kic, quarters, flux_array
############################################################################################


############################################################################################
## This function sets up command-line options and arguments through the OptionParser class.
############################################################################################
def setup_input_options(parser):
    parser.add_option("-p", "--period", action="store", type="float", dest="period", help="[Required] Trial period (days).  There is no default value.")
    parser.add_option("-m", "--mindur", action="store", type="float", dest="min_duration", default=0.0416667, help="[Optional] Minimum transit duration to search for (days).  Default = 0.0416667 (1 hour).")
    parser.add_option("-d", "--maxdur", action="store", type="float", dest="max_duration", default=12.0, help="[Optional] Maximum transit duration to search for (days).  Default = 0.5 (12 hours).")
    parser.add_option("-b", "--nbins", action="store", type="int", dest="n_bins", default=100, help="[Optional] Number of bins to divide the lightcurve into.  Default = 100.")
    parser.add_option("--direction", action="store", type="int", dest="direction", default=0, help="[Optional] Direction of box wave to look for.  1=blip (top-hat), -1=dip (drop), 0=both (most significant).  Default = 0")
    parser.add_option("--printformat", action="store", type="string", dest="print_format", default="encoded", help="[Optional] Format of strings printed to screen.  Options are 'encoded' (base-64 binary) or 'normal' (human-readable ASCII strings).  Default = 'encoded'.")
############################################################################################


############################################################################################
## This function checks input arguments satisfy some minimum requirements.
############################################################################################
def check_input_options(parser,opts):
    if opts.period <= 0.0:
        parser.error("Period must be > 0.")
    if opts.min_duration <= 0.0:
        parser.error("Min. duration must be > 0.")
    if opts.max_duration <= 0.0:
        parser.error("Max. duration must be > 0.")
    if opts.max_duration <= opts.min_duration:
        parser.error("Max. duration must be > min. duration.")
    if opts.n_bins <= 0:
        parser.error("Number of bins must be > 0.")
############################################################################################


############################################################################################
## Determines the time baseline (range) of a lightcurve.  Input is a List of Lists comprised of [time, flux, flux_error].  Time is in days and the return value is also in days.
############################################################################################
def get_lc_baseline(lc):
    ## Note:  For now, it is assumed the input lightcurve List is sorted chronologically.  There should be a check on the input data for this, either in this program or in join_quarters.py (if there isn't one already).
    return (lc[-1])[0] - (lc[0])[0]
############################################################################################


############################################################################################
## Convert the requested duration (in days) to a duration in units of bins.
############################################################################################
def convert_duration_to_bins(duration_days, nbins, per, duration_type):
    ## Set type="min" if <duration_days> is a minimum duration, or set type="max" if it's a maximum duration.

    ## Note (SWF):  I would like to investigate this calculation in more detail later.

    if duration_type == 'min':
        duration_bins = max(int(duration_days*nbins/per),1)
    elif duration_type == 'max':
        duration_bins = int(duration_days*nbins/per) + 1
    else:
        ## Note (SWF): Need to add proper error handler here.
        duration_bins = 0

    return duration_bins
############################################################################################


############################################################################################
## This is the main routine.
############################################################################################
def main():
    ## Define input options.
    from optparse import OptionParser
    parser = OptionParser(usage="%prog -p [-m] [-d] [-b] [--direction]", version="%prog 1.0")
    setup_input_options(parser)
    
    ## Parse input options from the command line.
    opts, args = parser.parse_args()

    ## The trial period is a "required" "option", at least for now.  So, check to make sure it exists.
    if not opts.period:
        parser.error("No trial period specified.")

    ## Check input arguments are valid and sensible.
    check_input_options(parser,opts)

    ## Variables for some of the input options, since they may change later in the program.
    nbins = opts.n_bins
    trial_period = opts.period
    direction = opts.direction

    ## Read in the KIC ID, Quarter, and lightcurve data from standard input.
    input_data = read_mapper_output(sys.stdin)

    ## Peel out the Kepler ID, Quarters, and lightcurve from the input_data for use.
    ## Note:  The lightcurve is stored as a List of Lists comprised of [time, flux, flux_error].
    for k, q, f in input_data:
        kic_id = k
        quarters = q
        lightcurve = f

    ## Calculate the time baseline of this lightcurve (this will be in days).
    lightcurve_timebaseline = get_lc_baseline(lightcurve)

    ## Convert the min and max transit durations to units of bins from units of days.
    mindur = convert_duration_to_bins(opts.min_duration, nbins, trial_period, duration_type="min")
    maxdur = convert_duration_to_bins(opts.max_duration, nbins, trial_period, duration_type="max")

    ## Define the minimum "r" value.  Note that "r" is the sum of the weights on flux at full depth.
    ## Note:  The sample rate of Kepler long-cadence data is (within a second) 0.02044 days.
    lc_samplerate = 0.02044
    r_min = max(1,int(mindur/lc_samplerate))

    ## Note (SWF):  Left off on first-pass here.

    # format data arrays
    array = numpy.array(lightcurve)
    fixedArray = numpy.isfinite(array[:,1])
    array = array[fixedArray]
    time = array[:,0]
    flux = array[:,1]
    n = time.size
    fluxSet = flux - numpy.mean(flux)
    # divide input time array into segments
    segments = [(x,time[x:x+int(trial_period/lc_samplerate)]) for x in xrange(0,len(time),int(trial_period/lc_samplerate))]
    # create outputs
    # I'm just putting these in as a placeholder for now.
    # I don't know what the actual outputs for this should be
    # I just stole these array names from pavel's code.
    srMax = numpy.array([])
    transitDuration = numpy.array([])
    transitPhase = numpy.array([])
    transitMidTime = numpy.array([])
    transitDepth   = numpy.array([])
    for i,seg in enumerate(segments):
        txt = 'KIC'+kic_id+'|Segment  '+ str(i) + ' out of ' +str(len(segments))
        logger.info(txt)
        l,segs = seg
        # bin data points
        segs = numpy.array(segs)
        n = segs.size
	# make sure bins not greater than data points in period
        nbins = int(opts.n_bins)
        if n < nbins:
            nbins = n
            mindur = convert_duration_to_bins(opts.min_duration, nbins, trial_period, duration_type="min")
            maxdur = convert_duration_to_bins(opts.min_duration, nbins, trial_period, duration_type="max")
        ppb = numpy.zeros(nbins)
        binFlx = numpy.zeros(nbins)
        # normalize phase
        # the following line will not maintain absolute phase because it redefines it every segment
        segSet = segs - segs[0]
        phase = segSet/trial_period - numpy.floor(segSet/trial_period)
        bin = numpy.floor(phase * nbins)
        for x in xrange(n):
            ppb[int(bin[x])] += 1
            # l is carried through from the original definition of the segments to make sure time segments sync up with their respective flux indices.
            binFlx[int(bin[x])] += fluxSet[l+x]
            # remove mean flux segment by segment (use a detrended flux eventually)
            binFlx = binFlx - numpy.mean(binFlx)
                    
        srMax = numpy.append(srMax, numpy.nan)
        transitDuration = numpy.append(transitDuration, numpy.nan)
        transitPhase = numpy.append(transitPhase, numpy.nan)
        transitMidTime = numpy.append(transitMidTime, numpy.nan)
        transitDepth   = numpy.append(transitDepth  , numpy.nan)
        # determine srMax
        for i1 in range(nbins):
            s = 0
            r = 0
            for i2 in range(i1, i1 + maxdur + 1):
                s += binFlx[i2%nbins]
                r += ppb[i2%nbins]
                if i2 - i1 > mindur and r >= r_min and direction*s >= 0:
                    sr = 1 * (s**2 / (r * (n - r)))
                    if sr > srMax[-1] or numpy.isnan(srMax[-1]):
                        srMax[-1] = sr
                        transitDuration[-1] = i2 - i1 + 1
                        transitPhase[-1] = i1
                        transitPhase[-1] = i1
                        transitDepth[-1] = -s*n/(r*(n-r))
                        transitMidTime[-1] = segs[0] + 0.5*(i1+i2)*trial_period/nbins
    # format output
    srMax = srMax**.5
        
    # Print output.
    if opts.print_format == 'encoded':
        print "\t".join(map(str,[kic_id, encode_arr(srMax),
                                 encode_arr(transitPhase),
                                 encode_arr(transitDuration),
                                 encode_arr(transitDepth),
                                 encode_arr(transitMidTime)]))
    elif opts.print_format == 'normal':
        print "\t".join(map(str,['Segment','srMax', 'transitPhase', 'transitDuration', 'transitDepth', 'transitMidTime']))
        for i,seq in enumerate(segments):
            print "\t".join(map(str,[i, srMax[i], transitPhase[i], transitDuration[i], transitDepth[i], transitMidTime[i]]))
                
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()
############################################################################################
