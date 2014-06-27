#!/usr/bin/env python

import numpy as np
import bls_pulse as bp


n, nbins = (10000, 10)
segsize = 0.1
binsize = segsize / nbins

time = np.sort(np.random.uniform(size=(n,)))
flux = np.ones_like(time)
fluxerr = np.zeros_like(time)

stime = np.zeros((nbins,), dtype='float64')
sflux = np.zeros((nbins,), dtype='float64')
sfluxerr = np.zeros((nbins,), dtype='float64')
samples = np.zeros((nbins,), dtype='float64')


###########################################################################
# Test for segment 0 (the easiest one)
###########################################################################
which = 0

save = bp.__get_binned_segment(time, flux, fluxerr, nbins, segsize, n, which, 0, 
    stime, sflux, sfluxerr, samples)

ndx = np.where((time >= segsize * which) & (time < segsize * (which + 1)))
t = time[ndx]
temp = []

for i in xrange(nbins):
    ndx = np.where((t >= (segsize * which) + (binsize * i)) & 
        (t < (segsize * which) + (binsize * (i + 1))))
    temp.append(np.mean(t[ndx]))

print stime
print np.array(temp)
print np.allclose(stime, temp)
print


###########################################################################
# Test for segment 1
###########################################################################
which = 1

stime[:] = 0.
sflux[:] = 0.
sfluxerr[:] = 0.
samples[:] = 0.

print 'saved index:', save
save = bp.__get_binned_segment(time, flux, fluxerr, nbins, segsize, n, which, save,
    stime, sflux, sfluxerr, samples)

ndx = np.where((time >= segsize * float(which)) & (time < segsize * float(which + 1)))
t = time[ndx]
temp = []

for i in xrange(nbins):
    start = segsize * float(which) + (binsize * float(i))
    end = start + binsize
    ndx = np.where((t >= start) & (t < end))
    temp.append(np.mean(t[ndx]))

print stime
print np.array(temp)
print np.allclose(stime, temp)
print

