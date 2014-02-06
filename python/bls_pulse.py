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
## This function transforms an array into compressed base-64 strings.
############################################################################################
def encode_arr(arr):
    #64bit encodes numpy arrays
    return base64.b64encode(compress(simplejson.dumps(arr.tolist())))
############################################################################################


############################################################################################
## Determines the time baseline (range) of a lightcurve.  Input is a List of Lists comprised of [time, flux, flux_error].  Time is in days and the return value is also in days.
############################################################################################
def get_lc_baseline(lc):
    ## Note:  For now, it is assumed the input lightcurve List is sorted chronologically.  There should be a check on the input data for this, either in this program or in join_quarters.py (if there isn't one already).
    return (lc[-1])[0] - (lc[0])[0]
############################################################################################


############################################################################################
## Convert the requested duration (in days) to a duration in (full) units of bins.  I round down for min and round up for max, but I am not 100% that's what we want to necessarily be doing here.  Either way, I preferred being consistent than relying on pure rounding like it was done previously.
############################################################################################
def convert_duration_to_bins(duration_days, nbins, segment_size, duration_type):
    ## Set type="min" if <duration_days> is a minimum duration, or set type="max" if it's a maximum duration.

    if duration_type == 'min':
        ## This was the way it was calculated originally.
        ## duration_bins = max(int(duration_days*nbins/segment_size),1)
        ## Here is SWF's version as he understands it.
        duration_bins = max(int(math.floor(duration_days*nbins/segment_size)),1)
    elif duration_type == 'max':
        ## This was the way it was calculated originally.
        ## duration_bins = max(int(duration_days*nbins/segment_size),1)
        ## Here is SWF's version as he understands it.
        duration_bins = max(1,min(int(math.ceil(duration_days*nbins/segment_size)), nbins))
    else:
        ## Note (SWF): Need to add proper error handler here.
        duration_bins = 0

    return duration_bins
############################################################################################


############################################################################################
## Convert the requested duration (in days) to a duration in units of bins.
############################################################################################
def calc_sr_max(n, nbins, mindur, maxdur, r_min, direction, trial_segment, binFlx, ppb, segs):

    ## Note (SWF):  I want to double check the math here matches what is done in Kovacs et al. (2002).  On the TO-DO list...

    ## Initialize output values to NaN.
    sr = numpy.nan
    thisDuration = numpy.nan
    thisPhase = numpy.nan
    thisDepth = numpy.nan
    thisMidTime = numpy.nan

    ## Initialize the "best" Signal Residue to NaN.
    best_SR = numpy.nan
    
    for i1 in range(nbins):
        s = 0
        r = 0
        for i2 in range(i1, min(i1 + maxdur + 1,nbins)):
            s += binFlx[i2]
            r += ppb[i2]
            if i2 - i1 > mindur and r >= r_min and direction*s >= 0:
                sr = 1 * (s**2 / (r * (n - r)))
                if sr > best_SR or numpy.isnan(best_SR):
                    best_SR = sr
                    thisDuration = i2 - i1 + 1
                    thisPhase = i1
                    thisDepth = -s*n/(r*(n-r))
                    thisMidTime = segs[0] + 0.5*(i1+i2)*trial_segment/nbins
    ## Return a tuple containing the Signal Residue and corresponding signal information.  If no Signal Residue was calculated in the loop above, then these will all be NaN's.
    return (best_SR, thisDuration, thisPhase, thisDepth, thisMidTime)
############################################################################################


############################################################################################
## This is the main routine.
############################################################################################
def main(segment_size, input_string=None, min_duration=0.0416667, max_duration=0.5, n_bins=100, direction=0, print_format="encoded", verbose=False):

    if not input_string:
        ## Read in the KIC ID, Quarter, and lightcurve data from standard input, *if* it is not supplied through the input options.
        input_data = read_mapper_output(sys.stdin)
    else:
        input_data = read_mapper_output(input_string)

    ## The number of bins can sometimes change, so make a working copy so that the original value is still available.
    nbins = n_bins

    ## Peel out the Kepler ID, Quarters, and lightcurve from the input_data for use.
    ## Note:  The lightcurve is stored as a List of Lists comprised of [time, flux, flux_error].
    for k, q, f in input_data:
        kic_id = k
        quarters = q
        lightcurve = f

        ## Calculate the time baseline of this lightcurve (this will be in days).
        lightcurve_timebaseline = get_lc_baseline(lightcurve)

        ## Convert the min and max transit durations to units of bins from units of days.
        mindur = convert_duration_to_bins(min_duration, nbins, segment_size, duration_type="min")
        maxdur = convert_duration_to_bins(max_duration, nbins, segment_size, duration_type="max")

        ## Define the minimum "r" value.  Note that "r" is the sum of the weights on flux at full depth.
        ## Note:  The sample rate of Kepler long-cadence data is (within a second) 0.02044 days.
        lc_samplerate = 0.02044
        r_min = max(1,int(mindur/lc_samplerate))

        ## Extract lightcurve information and mold it into numpy arrays.
        ## First identify which elements are not finite and remove them.
        lc_nparray = numpy.array(lightcurve)
        isFiniteArr = numpy.isfinite(lc_nparray[:,1])
        lc_nparray = lc_nparray[isFiniteArr]
        time = lc_nparray[:,0]
        flux = lc_nparray[:,1]
        
        ## Calculate mean of the flux.
        mean_flux_val = numpy.mean(flux)

        ## Create a version of the flux that has had the mean subtracted.
        flux_minus_mean = flux - mean_flux_val

        ## Divide the input time array into segments.
        segments = [(x,time[x:x+int(segment_size/lc_samplerate)]) for x in xrange(0,len(time),int(segment_size/lc_samplerate))]

        ## Initialize storage arrays for output values.  We don't know how many signals we will find, so for now these are instantiated without a length and we make use of the (more inefficient) "append" method in numpy to grow the array.  This could be one area that could be made more efficient if speed is a concern, e.g., by making these a sufficiently large size, filling them in starting from the first index, and then remove those that are empty at the end.  A sufficiently large size could be something like the time baseline of the lightcurve divided by the min. transit duration being considered, for example.
        ## I think we sort of do now how long they are going to be, we are finding the best signal for each segment so it'll come out equal to the number of segments. It was just programmed this way, probably inefficient though.
        srMax = numpy.array([])
        transitDuration = numpy.array([])
        transitPhase = numpy.array([])
        transitMidTime = numpy.array([])
        transitDepth   = numpy.array([])

        ## For each segment of this lightcurve, bin the data points into appropriate segments, normalize the binned fluxes, and calculate SR_Max.  If the new SR value is greater than the previous SR_Max value, store it as a potential signal.
        ## NOTE: "sr" is the Signal Residue as defined in the original BLS paper by Kovacs et al. (2002), A&A, 391, 377.
        for i,seg in enumerate(segments):
            ## Print progress information to screen, if verbose is set.
            if verbose:
                txt = 'KIC'+kic_id+'|Segment  '+ str(i+1) + ' out of ' +str(len(segments))
                logger.info(txt)

            ## Default this segments output values to NaN.  If a valid SR_Max is found, these will be updated with finite values.
            srMax = numpy.append(srMax, numpy.nan)
            transitDuration = numpy.append(transitDuration, numpy.nan)
            transitPhase = numpy.append(transitPhase, numpy.nan)
            transitMidTime = numpy.append(transitMidTime, numpy.nan)
            transitDepth   = numpy.append(transitDepth, numpy.nan)

            ## Bin the data points.
            l,segs = seg
            segs = numpy.array(segs)
            n = segs.size

            ## Make sure the number of bins is not greater than the number of data points in this segment.
            nbins = int(n_bins)
            if n < nbins:
                nbins = n
                mindur = convert_duration_to_bins(min_duration, nbins, segment_size, duration_type="min")
                maxdur = convert_duration_to_bins(max_duration, nbins, segment_size, duration_type="max")
            ppb = numpy.zeros(nbins)
            binFlx = numpy.zeros(nbins)

            ## Normalize the phase.
            ## Note: the following line will not maintain absolute phase because it redefines it every segment.
            segSet = segs - segs[0]
            phase = segSet/segment_size - numpy.floor(segSet/segment_size)
            bin = numpy.floor(phase * nbins)

            for x in xrange(n):
                ppb[int(bin[x])] += 1
                ## "l" is carried through from the original definition of the segments to make sure time segments sync up with their respective flux indices.
                binFlx[int(bin[x])] += flux_minus_mean[l+x]
                ## Remove the mean flux on a segment by segment basis.
                ## Note: We should use a detrended flux eventually.
                binFlx = binFlx - numpy.mean(binFlx)
            
            ## Determine SR_Max.  The return tuple consists of:
            ##      (Signal Residue, Signal Duration, Signal Phase, Signal Depth, Signal MidTime)
            sr_tuple = calc_sr_max(n, nbins, mindur, maxdur, r_min, direction, segment_size, binFlx, ppb, segs)
            ## If the Signal Residue is finite, then we need to add these parameters to our output storage array.
            if numpy.isfinite(sr_tuple[0]):
                srMax[-1] = sr_tuple[0]
                transitDuration[-1] = sr_tuple[1]
                transitPhase[-1] = sr_tuple[2]
                transitDepth[-1] = sr_tuple[3]
                transitMidTime[-1] = sr_tuple[4]
                
        ## Take the square root of the Signal Residue.
        srMax = srMax**.5
        
        ## Print output.
        if print_format == 'encoded':
            print "\t".join(map(str,[kic_id, encode_arr(srMax),
                                     encode_arr(transitPhase),
                                     encode_arr(transitDuration),
                                     encode_arr(transitDepth),
                                     encode_arr(transitMidTime)]))
        elif print_format == 'normal':
            print "-" * 80
            print "Kepler " + kic_id
            print "Quarters: " + quarters
            print "-" * 80
            print "\t".join(map(str,['Segment','srMax', 'transitPhase', 'transitDuration', 'transitDepth', 'transitMidTime']))
            for ii,seq in enumerate(segments):
                print "\t".join(map(str,[ii, srMax[ii], transitPhase[ii], transitDuration[ii], transitDepth[ii], transitMidTime[ii]]))
            print "-" * 80
            print "\n"

        ## Return each segments' transit event.

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()
############################################################################################
