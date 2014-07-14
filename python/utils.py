# -*- coding: utf-8 -*-

'''
This module contains functions that are common to several other modules in this
directory.
'''

import json
import base64
import zlib
import numpy as np


def boxcar(time, duration, depth, midtime):
    '''
    General function for producing a boxcar signal; useful for plotting.
    '''
    ndx = np.where((time >= midtime - duration / 2.) & (time <= midtime + duration / 2.))
    flux = np.zeros_like(time)
    flux[ndx] += depth

    return flux


def bin_segment_slow(time, flux, fluxerr, nbins, segstart, segend):
    '''
    Returns a binned segment. This should not be used in the pipeline! It is
    useful for plotting individual segments and debugging.

    See http://stackoverflow.com/questions/6163334/binning-data-in-python-with-scipy-numpy
    '''
    bin_slices = np.linspace(segstart, segend, nbins + 1)

    ndx = np.where((time >= segstart) & (time < segend))
    bin_memberships = np.digitize(time[ndx], bin_slices)
    binned_times = [time[ndx][bin_memberships == i].mean() for i in xrange(1, len(bin_slices))]
    binned_fluxes = [flux[ndx][bin_memberships == i].mean() for i in xrange(1, len(bin_slices))]
    binned_errors = [fluxerr[ndx][bin_memberships == i].mean() for i in xrange(1, len(bin_slices))]

    return np.array(binned_times, dtype='float64'), np.array(binned_fluxes, dtype='float64'), \
        np.array(binned_errors, dtype='float64')


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


def extreme(a, b):
    '''

    '''
    return a if (abs(a) > abs(b)) else b


def extreme_vec(arr):
    '''

    '''
    ndx = np.nanargmax(np.absolute(arr))
    return arr[ndx]

