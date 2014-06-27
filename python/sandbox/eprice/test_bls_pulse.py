#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
The simplest possible unittest for bls_pulse_binned. Take a single segment with a single
event and no noise and attempt to recover its parameters.
'''

import numpy as np
import bls_pulse as bp
import matplotlib.pyplot as plt


# Define a time baseline and flux with no error.
time = np.linspace(0., 2., 10000)
flux = np.ones_like(time)
fluxerr = np.zeros_like(time)
samples = np.ones_like(time)

# Inject the event.
d, r, m = (0.2, 0.4, 1.3)
start = m - d / 2.
end = m + d / 2.
ndx = np.where((time > start) & (time < end))
flux[ndx] = 1. - r

print 'Event parameters:'
print 'duration =', d
print 'depth =', r
print 'midtime =', m
print

nbins, segsize, mindur, maxdur = (100, 0.2, 0.04, 0.5)
srsq, duration, depth, midtime = bp.bls_pulse_main(time, flux, fluxerr, nbins,
    segsize, mindur, maxdur)

ndx = np.argmax(srsq)
print 'best duration =', duration.ravel()[ndx]
print 'best depth =', depth.ravel()[ndx]
print 'best midtime =', midtime.ravel()[ndx]

