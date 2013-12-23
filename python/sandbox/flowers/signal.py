import sys
import base64
import numpy
from zlib import decompress, compress
import simplejson
from random import gauss
from optparse import OptionParser
#generates fake outputs for testing. Currently creates a zero noise square wave.
#the 20000 as seen below is the total data points
#the 200 as seen below is the number of data points per period
#the 100 as seen below is just the number of periods
#the 20 as seen below is the length of the transit in data points
#the 30 as seen below is the phase shift of the transit in data points
#-10 is an arbitrary depth for the transit
#when I have less pressing things to do this code will eventually have built in options and random noise and stuff. I just don't care right now.

def main(separator = '\t'):
    parser = OptionParser()
    parser.add_option("-l","--periodlength", type='int')
    parser.add_option("-n","--datapoints", type='int')
    parser.add_option("-t","--transitlength", type='int')
    parser.add_option("-p","--phaseshift", type='int', default=0)
    parser.add_option("-d","--depth", type='float', default=1)
    parser.add_option("-s","--sigma", type='float', default=1)
    opts, args = parser.parse_args()
    parser.add_option("-m","--noise", type='float', default=opts.depth)
    parser.add_option("-u","--timeperpoint", type='float', default=.02044)
    opts, args = parser.parse_args()
    l=opts.periodlength
    n=opts.datapoints
    t=opts.transitlength
    p=opts.phaseshift
    d=opts.depth
    s=opts.sigma
    m=opts.noise
    u=opts.timeperpoint
    kic = 'your mom lol'
    q = '1234567'
    data = numpy.array([[x * u, 0] for x in xrange(n)])
    for y in xrange(n/l + 1):
        for x in xrange(min(t,n-y*l-p)):
			data[(y*l + x + p)][1] -= d
    for x in xrange(n):
        data[x][1] += gauss(0,s)*m
    print "%s%s%s%s%s" % (kic, separator, q, separator, encode_list(data))
    
def encode_list(flux_list):
    return base64.b64encode(compress(simplejson.dumps(flux_list.tolist())))
	
if __name__ == "__main__":
    main()