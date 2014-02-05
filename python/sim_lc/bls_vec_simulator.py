import numpy as np
import pandas as pd

def bls_vec_simulator(period=5, transit_ratio=0.025, transit_depth=0.010, phase=0.3, signal_to_noise=1, n_samples=3000, time_span=60):
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
    phase : float
        Orbital phase corresponding to the *start* of the transit (specify between 0. and 1.)
    signal_to_noise : float
        Ratio of transit_depth to white noise standard deviation
    n_samples : integer
        Number of samples, assumes fixed sampling rate
    time_span : integer
        Number of days

    Returns
    =======
    A Dictionary that contains the following keys and data structures:
       lc : light_curve [DataFrame]: A pandas DataFrame consisting of ndarrays where the first column is the flux, the second column is the flux error, and the index is the timestamps of each data point.
       transit_times: transittimes [list]: A List of transit mid-point times, used for comparing results from other programs to see which transits were found.
       transit_depths: depths [list]: A List of transit depths, used for comparing results from other programs to see which transits were found.
       transit_durations: durations [list]: A List of transit durations (in hours), used for comparing results from other programs to see which transits were found.
    """

    time = pd.Index(np.linspace(0, time_span, num=n_samples), name="Time [d]")
    transit_phase = np.remainder(time, period)/period
    white_noise_std = transit_depth/signal_to_noise

    # initialize flux to 0
    light_curve = pd.DataFrame({
                                   "flux":       0, 
                                   "flux_error": white_noise_std
                               }, index=time)

    # include transit
    ## NOTE (SWF): There is a bug here because if the startings phase of the transit is close to 1.0 and the duration pushes it over, it will not wrap properly as written.
    light_curve.flux[(transit_phase > phase) & (transit_phase < (phase + transit_ratio))] -= transit_depth

    # remove mean
    light_curve.flux -= light_curve.flux.mean()

    # add white noise
    light_curve.flux += np.random.normal(loc=0, scale=white_noise_std, size=n_samples)

    # create array of transit midpoint times, depths, and durations for passing back to calling program.  used so the calling program can compare results to the (known) transit parameters created here.
    # first, calculate the precise *phase* of central transit
    phase_t0 = (phase+transit_ratio - phase) / 2. + phase
    
    
    transittimes = []
    depths = []
    durations = []

    return {'lc':light_curve, 'transit_times':transittimes, 'transit_depths':depths, 'transit_durations':durations}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    bls_vec_simulator()
