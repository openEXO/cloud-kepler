#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A more advanced Reducer, using Python iterators and generators.
From http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/
'''

import sys
import string
import logging
import numpy as np
from itertools import groupby
from operator import itemgetter
from utils import read_mapper_output, encode_list

# Basic logging configuration.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    # input comes from STDIN (standard input)
    data = read_mapper_output(sys.stdin, uri=True)

    current_kic = None
    all_quarters = list()

    for kic, q, time, flux, fluxerr in data:
        if (current_kic != kic and current_kic is not None) or \
        (current_kic == kic and q in all_quarters):
            # Starting a new ID. Print out the old results and reset.
            # We start a new ID whenever the KIC ID changes *or* if a quarter
            # repeats for the same star.
            current_kic = current_kic + '_' + \
                ''.join(np.random.choice(list(string.lowercase), size=(4,)))
            print '\t'.join([str(current_kic), str(all_quarters), encode_list(concatenated_time),
                encode_list(concatenated_flux), encode_list(concatenated_eflux)])
            current_kic = None

        if current_kic is None:
            # First ID in the list or starting a new ID.
            current_kic = kic

            all_quarters = list()
            concatenated_time = list()
            concatenated_flux = list()
            concatenated_eflux = list()

        all_quarters.append(q)
        concatenated_time.extend(time)
        concatenated_flux.extend(flux)
        concatenated_eflux.extend(fluxerr)

    # Need one last print statement at the end to make sure we got the last "in-progress"
    # concatenation.
    if current_kic is not None:
        current_kic = current_kic + '_' + \
            ''.join(np.random.choice(list(string.lowercase), size=(4,)))
        print '\t'.join([str(current_kic), str(all_quarters), encode_list(concatenated_time),
            encode_list(concatenated_flux), encode_list(concatenated_eflux)])

