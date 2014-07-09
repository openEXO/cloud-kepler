#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A more advanced Reducer, using Python iterators and generators.
From http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/
'''

import sys
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

    # groupby groups multiple quarters together for each Kepler ID
    #   current_kic is current Kepler ID
    #   group - iterator yielding all ["&lt;current_word&gt;", "&lt;count&gt;"] items

    for current_kic, group in groupby(data, itemgetter(0)):
        try:
            all_quarters = [[q, time, flux, eflux] for _, q, time, flux, eflux in group]
            concatenated_time = list()
            concatenated_flux = list()
            concatenated_eflux = list()

            for _, t, f, e in all_quarters:
                concatenated_time.extend(t)
                concatenated_flux.extend(f)
                concatenated_eflux.extend(e)

            all_q = [q for q, _, _, _ in all_quarters]
            print '\t'.join([str(current_kic), str(all_q), encode_list(concatenated_time),
                encode_list(concatenated_flux), encode_list(concatenated_eflux)])
        except ValueError:
            # count was not a number, so silently discard this item
            pass

