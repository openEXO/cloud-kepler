#!/usr/bin/env python
#import matplotlib
#matplotlib.use("agg")
import pandas as pd
import json
from zlib import decompress, compress
import base64
import logging
import sys
import math
from argparse import ArgumentParser
from collections import OrderedDict
from bls_pulse_vec import bls_pulse_vec

def read_mapper_output(file, separator='\t'):
    """Read stdin input"""
    for line in file:
        kic, quarters, flux_string = line.rstrip().split(separator)
        light_curve = pd.DataFrame(json.loads((decompress(base64.b64decode(flux_string)))), columns=["time", "flux", "flux_error"]).set_index("time")
        yield kic, quarters, light_curve

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

def setup_input_options(parser):
    parser.add_argument("-p", "--segment", action="store", type=float, dest="segment", 
        help="[Required] Trial segment (days).  There is no default value.")
    parser.add_argument("-m", "--mindur", action="store", type=float, dest="min_duration", 
        default=0.0416667, help="[Optional] Minimum transit duration to search for (days).  "
            "Default = 0.0416667 (1 hour).")
    parser.add_argument("-d", "--maxdur", action="store", type=float, dest="max_duration", 
        default=12.0, help="[Optional] Maximum transit duration to search for (days). "
            "Default = 0.5 (12 hours).")
    parser.add_argument("-b", "--nbins", action="store", type=int, dest="n_bins", default=100, 
        help="[Optional] Number of bins to divide the lightcurve into.  Default = 100.")
    parser.add_argument("-o", "--detrend-order", action="store", type=int, dest="detrend_order", 
        default=0, help="[Optional] Order of the polynomial detrending using PyKE.  Default = 0 "
        "(no detrending)")
    parser.add_argument("--direction", action="store", type=int, dest="direction", default=0, 
        help="[Optional] Direction of box wave to look for.  1=blip (top-hat), -1=dip (drop), "
            "0=both (most significant).  Default = 0")
    parser.add_argument("--printformat", action="store", type=str, dest="print_format", 
        default="encoded", help="[Optional] Format of strings printed to screen.  Options are "
            "'encoded' (base-64 binary) or 'normal' (human-readable ASCII strings).  Default "
            "= 'encoded'.")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=False, 
        help="[Optional] Turn on verbose messages/logging.  Default = False.")

def encode_arr(arr):
    """64bit encodes numpy arrays"""
    return base64.b64encode(compress(json.dumps(arr.tolist())))

def main():
    # NOTE: Adding a version number to ArgumentParser conflicts with -v flag that we have
    # defined to be a verbosity option. If the version number is important, change the "-v"
    # flag to be something else.
    parser = ArgumentParser(usage="%prog -p [-m] [-d] [-b] [--direction]")
    setup_input_options(parser)
    
    ## Parse input options from the command line.
    args = parser.parse_args()

    ## The trial segment is a "required" "option", at least for now.  So, check to make sure it exists.
    if not args.segment:
        parser.error("No trial segment specified.")

    ## Check input arguments are valid
    check_input_options(parser, args)

    input_data = read_mapper_output(sys.stdin)

    output = OrderedDict()
    pd.set_option('display.max_rows', None) # print all rows of dataframe
    for kic_id, quarters, light_curve in input_data:
        id_string = kic_id + quarters.replace(",","_").translate(None, "[]' ")
        output[id_string] = bls_pulse_vec(light_curve, args.segment, args.min_duration, 
            args.max_duration, args.n_bins, detrend_order=args.detrend_order)

        print "*"*20 + "   " + id_string
        print output[id_string]

if __name__ == "__main__":
    main()
    sys.exit(0)
