############################################################################################
## Place import commands and logging options.
############################################################################################import sys
import sys
import numpy
import base64
import logging
import simplejson
from zlib import decompress, compress
import math

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
############################################################################################



############################################################################################
## This function reads in data from the stream.
############################################################################################
def read_mapper_output(file, separator='\t'):
    for line in file:
        kic, quarters, lcfile, flux_string = line.rstrip().split(separator)
        flux_array = simplejson.loads((decompress(base64.b64decode(flux_string))))
        yield kic, quarters, flux_array
############################################################################################



############################################################################################
## This is the main routine.
############################################################################################
def main(separator="\t"):
    ## Define input options. ##
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--minper", action="store", type="float", dest="min_period", default=0.1, help="Minimum period to search for (days).  Default = 0.1 days.")
    parser.add_option("--maxper", action="store", type="float", dest="max_period", default=1000., help="Maximum period to search for (days).  Default = 1000 days.")
    parser.add_option("--mindur", action="store", type="float", dest="min_duration", default=1.0, help="Minimum transit duration to search for (hours).  Default = 1 hour.")
    parser.add_option("--maxdur", action="store", type="float", dest="max_duration", default=12., help="Maximum transit duration to search for (hours).  Default = 12 hours.")

    ## Parse input options. ##
    options, arguments = parser.parse_args()

    ## Read data from standard input. ##
    input_data = read_mapper_output(sys.stdin, separator=separator)

    ## Loop over each row in the input file.
    for kic, quarters, flux_array in input_data:
        print kic
        print quarters
        print flux_array[0]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()
############################################################################################
