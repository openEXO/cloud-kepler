import pandas as pd
import simplejson
from zlib import decompress, compress
import base64
import logging
import sys
import math
from optparse import OptionParser

def read_mapper_output(file, separator='\t'):
    """Read stdin input"""
    for line in file:
        kic, quarters, flux_string = line.rstrip().split(separator)
        light_curve = pd.DataFrame(simplejson.loads((decompress(base64.b64decode(flux_string)))), columns=["time", "flux", "flux_error"]).set_index("time")
        yield kic, quarters, light_curve

def setup_input_options(parser):
    parser.add_option("-p", "--segment", action="store", type="float", dest="segment", help="[Required] Trial segment (days).  There is no default value.")
    parser.add_option("-m", "--mindur", action="store", type="float", dest="min_duration", default=0.0416667, help="[Optional] Minimum transit duration to search for (days).  Default = 0.0416667 (1 hour).")
    parser.add_option("-d", "--maxdur", action="store", type="float", dest="max_duration", default=12.0, help="[Optional] Maximum transit duration to search for (days).  Default = 0.5 (12 hours).")
    parser.add_option("-b", "--nbins", action="store", type="int", dest="n_bins", default=100, help="[Optional] Number of bins to divide the lightcurve into.  Default = 100.")
    parser.add_option("--direction", action="store", type="int", dest="direction", default=0, help="[Optional] Direction of box wave to look for.  1=blip (top-hat), -1=dip (drop), 0=both (most significant).  Default = 0")
    parser.add_option("--printformat", action="store", type="string", dest="print_format", default="encoded", help="[Optional] Format of strings printed to screen.  Options are 'encoded' (base-64 binary) or 'normal' (human-readable ASCII strings).  Default = 'encoded'.")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="[Optional] Turn on verbose messages/logging.  Default = False.")

def encode_arr(arr):
    """64bit encodes numpy arrays"""
    return base64.b64encode(compress(simplejson.dumps(arr.tolist())))


def main():
    parser = OptionParser(usage="%prog -p [-m] [-d] [-b] [--direction]", version="%prog 1.0")
    setup_input_options(parser)
    
    ## Parse input options from the command line.
    opts, args = parser.parse_args()

    ## The trial segment is a "required" "option", at least for now.  So, check to make sure it exists.
    if not opts.segment:
        parser.error("No trial segment specified.")

    ## Check input arguments are valid
    check_input_options(parser,opts)

    input_data = read_mapper_output(sys.stdin)

    for kic_id, quarters, light_curve in input_data:
        bls_pulse_vec(light_curve, period, opts.min_duration, opts.max_duration, n_bins, detrend=detrend_mean_remove)
