import numpy
import simplejson
from zlib import decompress, compress
import base64
import logging
import sys
import math

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#This is the barest prototype of the bls pulse search. Basically just took peter_bls.py and removed all nonessential parts.
#Does not yet have full functionality and is not really integrated into the frame of the rest of our code. Needs much work.
#Completely untested but should currently give the best sr in the data set along with its duration and phase in bins. 
#Does not give depth or direction of signal.
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
    parser.add_option("-i","--qmin")
    parser.add_option("-q","--qmax")
    parser.add_option("-b","--nbins")
    opts, args = parser.parse_args()
    minbin = 5
    qmin = float(opts.qmin)
    qmax = float(opts.qmax)
    nbins = int(opts.nbins)
    mindur = max(int(qmin * nbins),1)
    maxdur = int(qmax * nbins) + 1
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
        t = timeSet[-1] + .02044
#bin data points
        ppb = numpy.zeros(nbins)
        binFlx = numpy.zeros(nbins)
        phase = timeSet/t - numpy.floor(timeSet/t)
        bin = numpy.floor(phase * nbins)
        for x in xrange(n):
            ppb[int(bin[x])] += 1
            binFlx[int(bin[x])] += fluxSet[x]
#determine srMax
        for i1 in range(nbins):
            s = 0
            r = 0
            for i2 in range(i1, maxdur+1):
                s += binFlx[i2%nbins]
                r += ppb[i2%nbins]
                if i2 - i1 + 1 >= mindur and r >= rmin:
                    sr = s**2 / (r * (n - r))
                    if sr > srMax or numpy.isnan(srMax):
                        srMax = sr
                        transitDuration = i2 - i1 + 1
                        transitPhase = i1
#format output
        srMax = srMax**.5
        print "\t".join(map(str,[kic, srMaxx transitPhase, transitDuration]))
		
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()
