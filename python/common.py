'''
This module contains functions that are common to several other modules in this
directory.
'''

import json
import base64
import zlib


def read_mapper_output(f, separator='\t'):
    '''
    Reads data from the input file, assuming the given separator, in base64 format;
    yields the decoded and split line. The format is kic_id, quarter, flux_array for each
    line.
    '''
    for line in f:
        kic, quarters, t, f, e = line.rstrip().split(separator)
        time = json.loads(zlib.decompress(base64.b64decode(t)))
        flux = json.loads(zlib.decompress(base64.b64decode(f)))
        fluxerr = json.loads(zlib.decompress(base64.b64decode(e)))
        yield kic, quarters, time, flux, fluxerr


def encode_array(arr):
    '''
    base64-encodes the given NumPy array.
    '''
    return base64.b64encode(zlib.compress(json.dumps(arr.tolist())))


def encode_list(lst):
    '''
    base64-encodes the given NumPy array.
    '''
    return base64.b64encode(zlib.compress(json.dumps(lst)))


def decode_array(s):
    '''
    base64-decode the given string.
    '''
    return json.loads(zlib.decompress(base64.b64decode(s)))

