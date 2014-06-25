'''
This module contains functions that are common to several other modules in this 
directory.
'''

import json
import base64
from zlib import decompress, compress


def read_mapper_output(f, separator='\t'):
    '''
    Reads data from the input file, assuming the given separator, in base64 format; 
    yields the decoded and split line. The format is kic_id, quarter, flux_array for each
    line.
    '''
    for line in f:
        kic, quarters, flux_string = line.rstrip().split(separator)
        flux_array = json.loads((decompress(base64.b64decode(flux_string))))
        yield kic, quarters, flux_array


def encode_arr(arr):
    '''
    base64-encodes the given NumPy array.
    '''
    return base64.b64encode(compress(json.dumps(arr.tolist())))


