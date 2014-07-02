import sys
import logging
import bls_pulse
import bls_pulse_vec
import get_data
import join_quarters
from configparser import SafeConfigParser, NoOptionError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def check_input_options(segment, min_duration, max_duration, n_bins):
    '''
    Performs sanity checks on several configuration parameters and raises `ValueError` if
    any of them are invalid.
    '''
    if segment <= 0.:
        raise ValueError('Segment size must be > 0.')
    if min_duration <= 0.:
        raise ValueError('Min. duration must be > 0.')
    if max_duration <= 0.:
        raise ValueError('Max. duration must be > 0.')
    if max_duration <= min_duration:
        raise ValueError('Max. duration must be > min. duration.')
    if n_bins <= 0:
        raise ValueError('Number of bins must be > 0.')


def main():
    '''
    This is the main routine.  It calls bls_pulse by passing all commands through standard 
    in as part of the processing "chain".
    '''
    if len(sys.argv) != 2:
        raise ValueError('usage: python drive_bls_pulse_config.py params.cfg')

    # Load the configuration file.
    defaults = {'min_duration':'0.0416667', 'max_duration':'0.5', 'n_bins':'100',
        'direction':'0', 'print_format':'encoded', 'verbose':'no', 'vectorized':'no'}
    cp = SafeConfigParser(defaults)
    cp.read(sys.argv[1])

    # Extract the parameters from the configuration file.
    try:
        segment = cp.getfloat('DEFAULT', 'segment')
        min_duration = cp.getfloat('DEFAULT', 'min_duration')
        max_duration = cp.getfloat('DEFAULT', 'max_duration')
        n_bins = cp.getint('DEFAULT', 'n_bins')
        direction = cp.getint('DEFAULT', 'direction')
        print_format = cp.get('DEFAULT', 'print_format')
        verbose = cp.getboolean('DEFAULT', 'verbose')
        vectorized = cp.getboolean('DEFAULT', 'vectorized')
    except (NoOptionError, ValueError):
        raise ValueError('Invalid input configuration file')

    # Sanity checks on input options.
    check_input_options(segment, min_duration, max_duration, n_bins)
    
    if vectorized:
        bls_pulse_vec.main(segment, None, min_duration, max_duration, n_bins, direction, 
            print_format, verbose)
    else:
        bls_pulse.main(segment, None, min_duration, max_duration, n_bins, direction, 
            print_format, verbose)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()

