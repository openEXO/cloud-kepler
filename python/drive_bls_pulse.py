############################################################################################
# Place import commands and logging options.
############################################################################################
import logging
from argparse import ArgumentParser
import bls_pulse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
############################################################################################


############################################################################################
# This function sets up command-line options and arguments through the OptionParser class.
############################################################################################
def setup_input_options(parser):
    parser.add_argument("-p", "--segment", action="store", type=float, dest="segment", 
        help="[Required] Trial segment (days).  There is no default value.")
    parser.add_argument("-m", "--mindur", action="store", type=float, dest="min_duration", 
        default=0.0416667, help="[Optional] Minimum transit duration to search for (days). "
            "Default = 0.0416667 (1 hour).")
    parser.add_argument("-d", "--maxdur", action="store", type=float, dest="max_duration", 
        default=12.0, help="[Optional] Maximum transit duration to search for (days). "
            "Default = 0.5 (12 hours).")
    parser.add_argument("-b", "--nbins", action="store", type=int, dest="n_bins", default=100, 
        help="[Optional] Number of bins to divide the lightcurve into.  Default = 100.")
    parser.add_argument("--direction", action="store", type=int, dest="direction", default=0, 
        help="[Optional] Direction of box wave to look for.  1=blip (top-hat), -1=dip (drop), "
            "0=both (most significant).  Default = 0")
    parser.add_argument("--printformat", action="store", type=str, dest="print_format", 
        default="encoded", help="[Optional] Format of strings printed to screen.  Options are "
            "'encoded' (base-64 binary) or 'normal' (human-readable ASCII strings).  Set to "
            "any other string (e.g., 'none') to supress output printing.  Default = 'encoded'.")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=False, 
        help="[Optional] Turn on verbose messages/logging.  Default = False.")
############################################################################################


############################################################################################
# This function checks input arguments satisfy some minimum requirements.
############################################################################################
def check_input_options(parser, args):
    if args.segment <= 0.0:
        parser.error("Segment size must be > 0.")
    if args.min_duration <= 0.0:
        parser.error("Min. duration must be > 0.")
    if args.max_duration <= 0.0:
        parser.error("Max. duration must be > 0.")
    if args.max_duration <= args.min_duration:
        parser.error("Max. duration must be > min. duration.")
    if args.n_bins <= 0:
        parser.error("Number of bins must be > 0.")
############################################################################################


############################################################################################
# This class defines a generic Exception to use for errors raised in DRIVE_MAKE_LC and is 
# specific to this module. It simply returns the given value when raising the exception, 
# e.g., raise DriveBLSPulseError("Print this string") -> __main__.MyError: 'Print this string.'
############################################################################################
class DriveBLSPulseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
############################################################################################


############################################################################################
# This is the main routine.  It calls bls_pulse by passing all commands through standard 
# in as part of the processing "chain".
############################################################################################
def main():
    # Define input options.
    parser = ArgumentParser()
    setup_input_options(parser)
    
    # Parse input options from the command line.
    args = parser.parse_args()

    # The trial segment is a "required" "option", at least for now. So, check to make sure 
    # it exists.
    if not args.segment:
        parser.error("No trial segment specified.")

    # Check input arguments are valid and sensible.
    check_input_options(parser, args)

    # Call bls_pulse.
    bls_pulse.main(args.segment, None, args.min_duration, args.max_duration, args.n_bins, 
        args.direction, args.print_format, args.verbose)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()
############################################################################################

