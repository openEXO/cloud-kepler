# -*- coding: utf-8 -*-

'''
This module contains functions that are common to several other modules in this
directory.
'''

import os
import sys
import json
import zlib
import base64
import logging
import traceback
import numpy as np
from detrend import polyfit
from numpy.polynomial import polynomial as poly

###########################################################################
# stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
###########################################################################
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}


class ColoredFormatter(logging.Formatter):
    '''
    Formatter compatible with Python ``logging`` module. Allows colored
    messages to be written to the terminal, determined by the level
    of the message (warning, error, etc.).
    '''
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)

###########################################################################


def setup_logging(fname):
    '''
    Standard way to set up logging for this library.

    :param fname: File name of the calling module (from ``__file__``)
    :type fname: str
    '''
    name = '.'.join(os.path.basename(fname).split('.')[:-1])

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    hdlr = logging.StreamHandler(sys.stderr)
    hdlr.setFormatter(ColoredFormatter('%(levelname)s:%(name)s %(message)s'))
    logger.addHandler(hdlr)

    return logger


def handle_exception(exc_tuple):
    '''
    If these commands are called as a pipe chain with bash, etc., the chain
    needs to be stopped with a ``sys.exit(1)`` call, which prevents printing
    the information about the exception we are used to. Call this function
    with the exception tuple to print out the traceback to STDERR before
    calling the exit.

    :param exc_tuple: Exception tuple (from ``sys.exc_info()``)
    :tupe exc_tuple: tuple
    '''
    exc_type, exc_value, exc_traceback = exc_tuple
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    sys.stderr.write(''.join(lines))
    sys.stderr.flush()


def boxcar(time, duration, depth, midtime):
    '''
    General function for producing a boxcar signal; useful for plotting.

    :param time: Vector of observation times
    :type time: np.ndarray
    :param duration: Duration of the signal
    :type duration: float
    :param depth: Depth of the signal
    :type depth: float
    :param midtime: Midtime of the signal
    :type midtime: float
    '''
    ndx = np.where((time >= midtime - duration / 2.) & (time <= midtime + duration / 2.))
    flux = np.zeros_like(time)
    flux[ndx] += depth

    return flux


def bin_and_detrend_slow(time, flux, fluxerr, nbins, segstart, segend):
    segsize = segend - segstart

    t1, f1, e1 = bin_single_segment_slow(time, flux, fluxerr, nbins,
        segstart - segsize, segstart)
    t2, f2, e2 = bin_single_segment_slow(time, flux, fluxerr, nbins,
        segstart, segend)
    t3, f3, e3 = bin_single_segment_slow(time, flux, fluxerr, nbins,
        segend, segend + segsize)

    t = np.concatenate((t1,t2,t3))
    f = np.concatenate((f1,f2,f3))
    e = np.concatenate((e1,e2,e3))

    ndx = np.where(np.isfinite(f))
    m = (segstart + segend) / 2.
    coeffs = polyfit.polyfit(t[ndx] - m, f[ndx], e[ndx], 3)
    trend = poly.polyval(t2 - m, coeffs)
    f_detrend = f2 / trend
    f_detrend -= 1.
    e_detrend = e2 / trend

    return t2, f2, e2, trend, f_detrend, e_detrend


def bin_single_segment_slow(time, flux, fluxerr, nbins, segstart, segend):
    '''
    Returns a binned segment. This should not be used in the pipeline! It is
    useful for plotting individual segments and debugging.

    See http://stackoverflow.com/questions/6163334/binning-data-in-python-with-scipy-numpy

    :param time: Vector of times
    :type time: np.ndarray
    :param flux: Vector of fluxes
    :type flux: np.ndarray
    :param fluxerr: Vector of flux errors
    :type fluxerr: np.ndarray
    :param nbins: Number of bins per segment
    :type nbins: int
    :param segstart: Start time of this segment
    :type segstart: float
    :param segend: End time of this segment
    :type segend: float

    :rtype: tuple
    '''
    bin_slices = np.linspace(segstart, segend, nbins + 1)

    ndx = np.where((time >= segstart) & (time < segend))

    if len(ndx[0]) == 0:
        return (np.array([], dtype='float64'), np.array([], dtype='float64'),
            np.array([], dtype='float64'))

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

    :param f: File to read; usually ``sys.stdin``
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

    :param f: File to read; usually ``sys.stdin``
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
    Calculate the extreme of two numbers; ``a`` if ``abs(a) > abs(b)``.

    :rtype: float
    '''
    return a if (abs(a) > abs(b)) else b


def extreme_vec(arr):
    '''
    Calculate the extreme of an array; defined as the value with the
    greatest absolute value.

    :rtype: float
    '''
    ndx = np.nanargmax(np.absolute(arr))
    return arr[ndx]

