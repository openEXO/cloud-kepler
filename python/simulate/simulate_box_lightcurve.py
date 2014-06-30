# -*- coding: utf-8 -*-

import numpy as np


def simulate_box_lightcurve(period, duration, depth, shift, sn, nsamples, baseline):
    '''

    '''
    # Calculate the time baseline as evenly spaced points up to the given baseline
    # value.
    time = np.linspace(0., baseline, nsamples)
    flux = np.ones_like(time)

    # This is a rough estimate of the per-point uncertainty.
    sigma = depth / sn
    fluxerr = sigma * np.ones_like(time)

    # We subtract the initial phase (assumed centered) and modulo by the period.
    # Add back half a duration so that the event begins at t = 0.
    t = np.mod(time - shift * period + duration / 2., period)

    # Find points that lie in the transit and fill in fluxes.
    ndx = np.where((t > 0.) & (t < duration))
    flux[ndx] = 1. - depth

    # Add in the random errors.
    flux += np.random.normal(0., sigma)

    # Calculate durations, depths, and midtimes.
    ntransits = np.ceil((baseline - shift * period) / period)
    m = period * (np.arange(ntransits) + shift)
    dp = depth * np.ones_like(m)
    du = duration * np.ones_like(m)

    return time, flux, fluxerr, du, dp, m

