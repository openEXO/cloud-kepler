import sys
import base64
import numpy
from zlib import decompress, compress
import simplejson
from random import gauss
from optparse import OptionParser
#maybe we should name this module something better.

def setup_input_options(parser):
#figure out all the parameters of your signal
#operates in units days, or will once i get to doing that, it's still in data points atm. i'm feeling sort of lazy.
    parser.add_option("-l","--periodlength", type='float')
    parser.add_option("-n","--timespan", type='float')
    parser.add_option("-t","--transitlength", type='float')
    parser.add_option("-p","--phaseshift", type='float', default=0)
    parser.add_option("-d","--depth", type='float', default=1)
    parser.add_option("-s","--sigma", type='float', default=1)
    opts, args = parser.parse_args()
    parser.add_option("-m","--noise", type='float', default=opts.depth)
	#one minute in days is default, I don't know how precise I should make this lol.
    parser.add_option("-u","--timeperpoint", type='float', default=.000694444)
    parser.add_option("-v","--timeperbin", type='float', default = .02044)
    opts, args = parser.parse_args()
    return opts.periodlength, opts.timespan, opts.transitlength, opts.phaseshift, opts.depth, opts.sigma, opts.noise, opts.timeperpoint, opts.timeperbin

def addsig(data,n,l,t,p,d):
#pretty simple, throws the signal you want into the data
    for y in data[:,0]:
       if y%l>=p and y%l<=p+t:
            data[numpy.where(data[:,0]==y)[0][0]][1] -= d
	
def adderr(data,n,s,m):
#adds random noise, my limited understanding of the gauss random function
#and of signal to noise ratios makes this part kind of rough.
#will need to be checked or refined, might be able to remove one of our input options.
#does approximately what it should though.
    for x in xrange(len(data[:,0])):
        data[x][1] += gauss(0,s)*m
		
def bin(data,v,u,n):
#bins data points to export sums across longer intervals like kepler does.
    data2 = numpy.array([[x * v, 0] for x in xrange(1,int(n/v + 1))])
    y = 0
	#tracks index we are on in bin array
    zet = 0
	#tracks how many time points have been thrown into bin point
    for z in data[:,0]:
        if data[:,0][z] <= data2[:,0][y]:
		    #add time point to bin point
            data2[y][1] += data[z][1]
            zet += 1
        elif data[:,0][z] <= data2[:,0][y] + u:
		    #split middle time point between two bin points and reset for next bin point
            m = (data2[:,0][y] + u - data[:,0][z])/u
            data2[y][1] += m*data[z][1]
            data2[y][1] /= zet + m
            y += 1
            zet = 1 - m
            data2[y][1] += zet*data[z][1]
    return data2
            
	
def main(separator = '\t'):
    parser = OptionParser()
    l,n,t,p,d,s,m,u,v = setup_input_options(parser)
    kic = 'your mom lol'
    q = '1234567'
    data = numpy.array([[x * u, 0] for x in xrange(1,int(n/u + 1))])
    addsig(data,n,l,t,p,d)
    adderr(data,n,s,m)
	#binning has not yet been fully debugged.
    #data2 = bin(data,v,u,n)
    print "%s%s%s%s%s" % (kic, separator, q, separator, encode_list(data))
    #print "%s%s%s%s%s" % (kic, separator, q, separator, encode_list(data2)) 
	
def encode_list(flux_list):
    return base64.b64encode(compress(simplejson.dumps(flux_list.tolist())))
	
if __name__ == "__main__":
    main()