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


def read_pipeline_output(f, separator='\t'):
    '''
    Reads data from the input file, assuming the given separator, in base64 format;
    yields the decoded and split line. The format for each line is KIC ID, quarter,
    segment_start, segment_end, srsq_dip, duration_dip, depth_dip, midtime_dip,
    srsq_blip, duration_blip, depth_blip, midtime_blip.

    :param f: File to read; usually stdin
    :type f: file
    :param separator: Sepearator between parts of an entry
    :type separator: str

    :rtype: tuple
    '''
    for line in f:
        kic, q, s1, s2, a1, a2, a3, a4, b1, b2, b3, b4 = line.rstrip().split(separator)

        segstart = decode_array(s1)
        segend = decode_array(s2)
        srsq_dip = decode_array(a1)
        duration_dip = decode_array(a2)
        depth_dip = decode_array(a3)
        midtime_dip = decode_array(a4)
        srsq_blip = decode_array(b1)
        duration_blip = decode_array(b2)
        depth_blip = decode_array(b3)
        midtime_blip = decode_array(b4)

        yield kic, q, segstart, segend, srsq_dip, duration_dip, depth_dip, midtime_dip, \
            srsq_blip, duration_blip, depth_blip, midtime_blip


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


def extreme(a, b, direction):
    '''

    '''
    return (a if (direction * a > direction * b) else b) if direction \
        else (a if (abs(a) > abs(b)) else b)


def extreme_vec(arr, direction):
    '''

    '''
    if direction == 1:
        return np.nanmax(arr)
    elif direction == -1:
        return np.nanmin(arr)
    else:
        ndx = np.nanargmax(np.absolute(arr))
        return arr[ndx]

