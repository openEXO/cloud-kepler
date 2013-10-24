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
    parser.add_option("-m","--mindur")
    parser.add_option("-d","--maxdur")
    parser.add_option("-b","--nbins")
    parser.add_option("-p","--per")
    ##per is period that we divide dataset into.
    #Bls pulse should return one best fitting pulse
    #for each subset of length per. units in days as always.
    opts, args = parser.parse_args()
    p = .02044
    #Kepler takes a data point every 1766 seconds or .02044 days.
	#from Section 2.1 of the Kepler Instrument Handbook. http://archive.stsci.edu/kepler/manuals/KSCI-19033-001.pdf
    mindur = float(opts.mindur)
    maxdur = float(opts.maxdur)
    rmin = max(1,int(mindur/p))
    nbins = int(opts.nbins)
    per = float(opts.per)
	#convert mindur and maxdur from units days to units bins
	#I wouldn't be terribly surprised if there was some slight inaccuracy here
	#I figure per/nbins is the number of days per bin in the segment, then to convert you should just divide by that
	#I have not tested it though, maybe that should happen. also maybe I'm just being paranoid.
    mindur = max(int(mindur*nbins/per),1)
    maxdur = int(maxdur*nbins/per) + 1
    input = read_mapper_output(sys.stdin)
    for kic, q, data in input:
#format data arrays
        array = numpy.array(data)
        fixedArray = numpy.isfinite(array[:,1])
        array = array[fixedArray]
        time = array[:,0]
        flux = array[:,1]
        n = time.size
        fluxSet = flux - numpy.mean(flux)
    #divide input time array into segments
        segments = [(x,time[x:x+int(per/p)]) for x in xrange(0,len(time),int(per/p))]
#create outputs
        #I'm just putting these in as a placeholder for now.
		#I don't know what the actual outputs for this should be
		#I just stole these array names from pavel's code.
        srMax = numpy.array([])
        transitDuration = numpy.array([])
        transitPhase = numpy.array([])
        for i,seg in enumerate(segments):
            txt = 'KIC'+kic+'|Segment  '+ str(i) + 'out of' +str(len(segments))
            logger.info(txt)
            l,segs = seg
#bin data points
            segs = numpy.array(segs)
            n = segs.size
	#make sure bins not greater than data points in period
            nbins = int(opts.nbins)
            if n < nbins:
                nbins = n
                mindur = max(int(mindur*nbins/per),1)
                maxdur = int(maxdur*nbins/per) + 1
            ppb = numpy.zeros(nbins)
            binFlx = numpy.zeros(nbins)
			#normalize phase
            segSet = segs - segs[0]
            phase = segSet/per - numpy.floor(segSet/per)
            bin = numpy.floor(phase * nbins)
            for x in xrange(n):
                ppb[int(bin[x])] += 1
			#l is carried through from the original definition of the segments to make sure time segments sync up with their respective flux indices.
                binFlx[int(bin[x])] += fluxSet[l+x]
            srMax = numpy.append(srMax, numpy.nan)
            transitDuration = numpy.append(transitDuration, numpy.nan)
            transitPhase = numpy.append(transitPhase, numpy.nan)
#determine srMax
            for i1 in range(nbins):
                s = 0
                r = 0
                for i2 in range(i1, i1 + maxdur + 1):
                    s += binFlx[i2%nbins]
                    r += ppb[i2%nbins]
                    if i2 - i1 > mindur and r >= rmin:
                        sr = s**2 / (r * (n - r))
                        if sr > srMax[-1] or numpy.isnan(srMax[-1]):
                            srMax[-1] = sr
                            transitDuration[-1] = i2 - i1 + 1
                            transitPhase[-1] = i1
#format output
        srMax = srMax**.5
        print "\t".join(map(str,[kic, encode_arr(srMax),
                                 encode_arr(transitPhase),
                                 encode_arr(transitDuration)]))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()
