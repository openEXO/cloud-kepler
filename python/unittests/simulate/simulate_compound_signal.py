# -*- coding: utf-8 -*-

import numpy as np


def simulate_compound_signal(baseline, nsamples, sigma, segsize, mindur, maxdur):
    '''

    '''
    # Calculate the time baseline as evenly spaced points up to the given baseline
    # value.
    time = np.linspace(0., baseline, nsamples, endpoint=False)
    flux = np.zeros_like(time)
    fluxerr = sigma * np.ones_like(time)

    nsegments = int(np.floor(baseline / segsize))

    du = np.empty((nsegments*2), dtype='float64')
    dp = np.empty((nsegments*2), dtype='float64')
    m = np.empty((nsegments*2), dtype='float64')

    j = 0

    for i in xrange(0, nsegments*2, 2):
        which = np.random.randint(2)

        du[i] = np.random.uniform(mindur, maxdur)
        start = np.random.uniform(0., segsize / 2. - du[i])
        dp[i] = np.random.uniform(0., 1.)
        m[i] = start + du[i] / 2. + (segsize * j)

        du[i+1] = np.random.uniform(mindur, maxdur)
        start = np.random.uniform(segsize / 2., segsize - du[i+1])
        dp[i+1] = np.random.uniform(0., 1.)
        m[i+1] = start + du[i+1] / 2. + (segsize * j)

        if which == 0:
            dp[i] *= -1.
        else:
            dp[i+1] *= -1.

        ndx = np.where((time >= m[i] - du[i] / 2.) & (time <= m[i] + du[i] / 2.))
        flux[ndx] += dp[i]
        ndx = np.where((time >= m[i+1] - du[i+1] / 2.) & (time <= m[i+1] + du[i+1] / 2.))
        flux[ndx] += dp[i+1]

        j += 1

    return time, flux, fluxerr, du, dp, m

