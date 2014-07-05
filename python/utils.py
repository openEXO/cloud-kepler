# -*- coding: utf-8 -*-

'''
This module contains functions that are common to several other modules in this
directory.
'''

import json
import base64
import zlib
import numpy as np


def read_mapper_output(f, separator='\t', uri=False):
    '''
    Reads data from the input file, assuming the given separator, in base64 format;
    yields the decoded and split line. The format is kic_id, quarter, time, flux, error
    for each line.
    '''
    for line in f:
        if uri:
            kic, q, uri, t, f, e = line.rstrip().split(separator)
        else:
            kic, q, t, f, e = line.rstrip().split(separator)

        time = decode_array(t)
        flux = decode_array(f)
        fluxerr = decode_array(e)
        yield kic, q, time, flux, fluxerr


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


def extreme(arr, direction):
    '''
    Returns the extreme of the array `arr`, defined as the minimum if `direction` = -1,
    the maximum if `direction` = +1, and the most extreme value if `direction` = 0.
    '''
    if direction == -1:
        return np.nanmin(arr)
    elif direction == 1:
        return np.nanmax(arr)
    elif direction == 0:
        ndx = np.nanargmax(np.absolute(arr))
        return arr[ndx]

