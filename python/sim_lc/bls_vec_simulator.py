import numpy as np
import pandas as pd

#################################################
class BLSVecSimError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
#################################################


#################################################
def find_phases_near_phase0(phases, phase_t0):
    """
    This program just finds the first pair of phases in a set of ordered *times* that straddle a given phase value.
    For example, if my phase array is [0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, ...] and I give it a phase_0 = 0.25, this function will give the *indexes* corresponding to the values of 0.2 and 0.3 above.  It takes into account the fact that the input list of phases may start already past the desired phase_0, and take into account the fact that you might easily have repeated (phase wrapped) values, and you want the very *first* pair of phases that straddle the desired phase_0 value.

    Returns the indexes of the straddled pair of phases in a tuple.

    *** NOTE:  This is not perfectly safe-guarded.  For example, right now I throw an error if either index is -1, since that would start looking at things at the end of the array.
    """
    # if the first phase in our list of transit_phases is already > phase_t0, we must skip ahead.
    i = 0
    if phases[i] > phase_t0:
        while phases[i] > phase_t0:
            i += 1

    # now we are starting at the first phase in our array of times that should be <= t_0.
    while phases[i] < phase_t0:
        i += 1
    # now the index "i" should contain the first transit phase that is > t_0, and the previous element should be the first phase that is < t_0
    if i > 0:
        return (i-1,i)
    else:
        raise BLSVecSimError("Error: Straddled index can not be the first element in the list.")
#################################################    


#################################################
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

    # add white noise
    light_curve.flux += np.random.normal(loc=0, scale=white_noise_std, size=n_samples)

    # remove mean
    light_curve.flux -= light_curve.flux.mean()

    # create array of transit midpoint times, depths, and durations for passing back to calling program.  used so the calling program can compare results to the (known) transit parameters created here.
    # first, calculate the precise *phase* of central transit, keeping in mind this might be > 1.0, but will not be > 2.0
    phase_t0 = phase + transit_ratio / 2.
    if phase_t0 > 1.0:
        phase_t0 -= 1.0
    # now get the precise time that corresponds to that specific phase by doing a simple interpolation.  Find the first phase in our list of phases that is closest to (but less than) the mid-point phase, and then the first phase that is closest to (but more than) the mid-point phase.  Use these two phases, and their associated times, to interpolate and find the first T0 in our array.
    phase_t0_indexes = find_phases_near_phase0(transit_phase, phase_t0)
    straddle_phases = [float(x) for x in transit_phase[phase_t0_indexes[0]:phase_t0_indexes[1]+1]]
    straddle_times = [float(x) for x in time[phase_t0_indexes[0]:phase_t0_indexes[1]+1]]
    time_t0 = np.interp(phase_t0, straddle_phases, straddle_times)
##    print straddle_phases[0], phase_t0, straddle_phases[1]
##    print straddle_times[0], time_t0, straddle_times[1]
    transittimes = []
    depths = []
    durations = []
    i = 0
    while i*period+time_t0 <= time[-1]:
        transittimes.append(i*period+time_t0)
        depths.append(transit_depth)
        durations.append(transit_ratio*period/24.)
        i+=1
    
    return {'lc':light_curve, 'transit_times':transittimes, 'transit_depths':depths, 'transit_durations':durations}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    bls_vec_simulator()
#################################################
