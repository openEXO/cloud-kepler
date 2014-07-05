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
    yields the decoded and split line. The format is KIC ID, quarter, [uri], time,
    flux, error for each line.

    :param f: File to read; usually stdin
    :type f: file
    :param separator: Sepearator between parts of an entry
    :type separator: str
    :param uri: Whether the URI is included on the line
    :type uri: bool

    :rtype: tuple
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
    base64-encodes the given numpy array.

    :param arr: Array to encode
    :type arr: numpy.ndarray

    :rtype: str
    '''
    return base64.b64encode(zlib.compress(json.dumps(arr.tolist())))


def encode_list(lst):
    '''
    base64-encodes the given Python list.

    :param lst: List to encode
    :type lst: list

    :rtype: str
    '''
    return base64.b64encode(zlib.compress(json.dumps(lst)))


def decode_array(s):
    '''
    base64-decode the given string.

    :param s: String to decode
    :type s: str

    :rtype: list
    '''
    return json.loads(zlib.decompress(base64.b64decode(s)))


def extreme(arr, direction):
    '''
    Returns the extreme of an array, defined as the minimum if `direction` = -1,
    the maximum if `direction` = +1, and the most extreme value if `direction` = 0.

    :param arr: Array for which to calculate the extreme
    :type arr: numpy.ndarray
    :param direction: Direction of the extreme; -1, 0, or 1
    :type direction: int

    :rtype: float
    '''
    if direction == -1:
        return np.nanmin(arr)
    elif direction == 1:
        return np.nanmax(arr)
    elif direction == 0:
        ndx = np.nanargmax(np.absolute(arr))
        return arr[ndx]

