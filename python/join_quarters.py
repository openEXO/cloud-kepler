#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A more advanced Reducer, using Python iterators and generators.
From http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/
'''

import sys
import string
import numpy as np
from itertools import groupby
from operator import itemgetter
from collections import OrderedDict
from utils import read_mapper_output, encode_list, setup_logging, handle_exception

# Basic logging configuration.
logger = setup_logging(__file__)


def main(instream=sys.stdin, outstream=None):
    data = read_mapper_output(instream, uri=True)

    for current_kic, group in groupby(data, itemgetter(0)):
        try:
            all_quarters = OrderedDict()

            # Patch to remove duplicate quarters.
            for _, q, time, flux, eflux in group:
                all_quarters[q] = (time, flux, eflux)

            concatenated_time = list()
            concatenated_flux = list()
            concatenated_eflux = list()

            keys, vals = (all_quarters.keys(), all_quarters.values())

            for k, v in zip(keys, vals):
                t, f, e = v
                concatenated_time.extend(t)
                concatenated_flux.extend(f)
                concatenated_eflux.extend(e)

            all_q = list(keys)
            outstream.write('\t'.join([str(current_kic), str(all_q),
                encode_list(concatenated_time),
                encode_list(concatenated_flux),
                encode_list(concatenated_eflux)]) + '\n')
        except ValueError:
            # count was not a number, so silently discard this item
            pass


if __name__ == '__main__':
    try:
        # input comes from STDIN (standard input)
        main(instream=sys.stdin, outstream=sys.stdout)
    except:
        handle_exception(sys.exc_info())
        sys.exit(1)

