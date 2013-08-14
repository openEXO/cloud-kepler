import numpy
import simplejson
from zlib import decompress, compress
import base64
import logging
import sys
import math

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#This code is incomplete and still being tested. So don't try to use it for anything serious.
def read_mapper_output(file, separator='\t'):
#reads data
    for line in file:
        kic, quarters,  flux_string = line.rstrip().split(separator)
        flux_array = simplejson.loads((decompress(base64.b64decode(flux_string))))
        yield kic, quarters, flux_array
		
def main():
#set up options and collect input parameters
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-m","--minper")
    parser.add_option("-p","--maxper")
    parser.add_option("-i","--qmin")
    parser.add_option("-q","--qmax")
    parser.add_option("-n","--nsearch")
    parser.add_option("-b","--nbins")
    opts, args = parser.parse_args()
    minbin = 5
    minper = float(opts.minper)
    maxper = float(opts.maxper)
    qmin = float(opts.qmin)
    qmax = float(opts.qmax)
    np = int(opts.nsearch)
    nbins = int(opts.nbins)
    mindur = max(int(qmin * nbins),1)
    maxdur = int(qmax * nbins) + 1
    trialPeriods = numpy.linspace(minper,maxper,np)
    input = read_mapper_output(sys.stdin)
    for kic, q, data in input:
#format data arrays
        array = numpy.array(data)
        fixedArray = numpy.isfinite(array[:,1])
        array = array[fixedArray]
        time = array[:,0]
        flux = array[:,1]
        n = time.size
        rmin = max(int(n * qmin),minbin)
        timeSet = time - time[0]
        fluxSet = flux - numpy.mean(flux)
#check period
        if maxper > timeSet[-1] - timeSet[0]:
            logger.error('ERROR --  maxper is larger than the time range of the input data')
            raise Exception
#create output arrays
        transitDuration = numpy.array([])
        transitPhase = numpy.array([])
        srMax = numpy.array([])
        for trial in trialPeriods:
#period iteration
	#make sure bins not greater than data points in period
            nbins = int(opts.nbins)
            if trial / .020433 + 1 < nbins:
                nbins = int(trial / .020433 + 1)
                mindur = max(int(qmin * nbins),1)
                maxdur = int(qmax * nbins) + 1
	#bin data points
            ppb = numpy.zeros(nbins)
            binFlx = numpy.zeros(nbins)
            phase = timeSet/trial - numpy.floor(timeSet/trial)
            bin = numpy.floor(phase * nbins)
            for x in xrange(n):
                ppb[int(bin[x])] += 1
                binFlx[int(bin[x])] += fluxSet[x]
	#prepare iteration
            srMax = numpy.append(srMax, numpy.nan)
            transitDuration = numpy.append(transitDuration, numpy.nan)
            transitPhase = numpy.append(transitPhase, numpy.nan)
	#determine srMax
            for i1 in range(nbins):
                s = 0
                r = 0
                for i2 in range(i1, maxdur+1):
                    s += binFlx[i2%nbins]
                    r += ppb[i2%nbins]
                    if i2 - i1 + 1 >= mindur and r >= rmin:
                        sr = s**2 / (r * (n - r))
                        if sr > srMax[-1] or numpy.isnan(srMax[-1]):
                            srMax[-1] = sr
                            transitDuration[-1] = i2 - i1 + 1
                            transitPhase[-1] = i1
#format output
        srMax = abs(srMax)**.5
        bestSr = numpy.max(srMax)
        t = numpy.nonzero(srMax == bestSr)
        print "\t".join(map(str,[kic, bestSr, trialPeriods[t], transitPhase[t], transitDuration[t]]))
		
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()
