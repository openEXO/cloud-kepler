import numpy as np
import pandas as pd

def simulate_box_lightcurve(period=5, transit_ratio=0.025, transit_depth=0.010, phase=0.3, signal_to_noise=1, n_samples=3000, time_span=60):
    """Simulate square-box light curve

    See Kovacs, 2002

    Parameters
    ==========
    period : int or float
        Transit period [days] (P0)
    transit_ratio : float
        Ratio of transit duration to period (q)
    transit_depth : float
        Depth of the transit [mag]
    signal_to_noise : float
        Ratio of transit_depth to white noise standard deviation
    n_samples : integer
        Number of samples, assumes fixed sampling rate
    time_span : integer
        Number of days

    Returns
    =======
    flux : array
        Square-box simulated flux with white noise
    """

    time = pd.Index(np.linspace(0, time_span, num=n_samples), name="Time [d]")
    transit_phase = np.remainder(time, period)/period
    white_noise_std = transit_depth/signal_to_noise

    # initialize flux to 0
    light_curve = pd.DataFrame({
                                   "flux":       0, 
                                   "flux_error": white_noise_std,
                               }, index=time)

    # include transit
    light_curve.flux[(transit_phase > phase) & (transit_phase < (phase + transit_ratio))] -= transit_depth

    # remove mean
    light_curve.flux -= light_curve.flux.mean()

    # add white noise
    light_curve.flux += np.random.normal(loc=0, scale=white_noise_std, size=n_samples)

    return light_curve
