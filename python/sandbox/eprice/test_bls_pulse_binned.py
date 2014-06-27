#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
The simplest possible unittest for bls_pulse_binned. Take a single segment with a single
event and no noise and attempt to recover its parameters.
'''

import numpy as np
import bls_pulse as bp


# Define a time baseline and flux with no error.
time = np.linspace(0., 2., 1000)
flux = np.ones_like(time)
fluxerr = np.zeros_like(time)

# Inject the event.
d, r, m = (0.9, 0.4, 1.3)
start = m - d / 2.
end = m + d / 2.
ndx = np.where((time > start) & (time < end))
flux[ndx] = 1. - r

print 'Event parameters:'
print 'duration =', d
print 'depth =', r
print 'midtime =', m
print

time = np.array(time)
flux = np.array(flux)
fluxerr = np.array(fluxerr)
samples = np.ones_like(time)

srsq = np.empty((1000,), dtype='float64')
duration = np.empty_like(srsq)
depth = np.empty_like(srsq)
midtime = np.empty_like(srsq)

bp.__bls_pulse_binned(time, flux, fluxerr, samples, 2., 0.05, 1.5, srsq, duration,
    depth, midtime)

ndx = np.argmax(srsq)
print 'best duration:', duration[ndx]
print 'best depth:', depth[ndx]
print 'best midtime:', midtime[ndx]

