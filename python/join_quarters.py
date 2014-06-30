#!/usr/bin/env python
'''
A more advanced Reducer, using Python iterators and generators.
From http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/
'''

import sys
import json
import base64
import zlib
import numpy as np
from itertools import groupby
from operator import itemgetter
from common import read_mapper_output, encode_list


def read_mapper_output(f, separator='\t'):
    '''
    Reads data from the input file, assuming the given separator, in base64 format;
    yields the decoded and split line. The format is kic_id, quarter, uri, time, flux,
    flux_error for each line.
    '''
    for line in f:
        kic, quarter, uri, t, f, e = line.rstrip().split(separator)
        time = json.loads(zlib.decompress(base64.b64decode(t)))
        flux = json.loads(zlib.decompress(base64.b64decode(f)))
        fluxerr = json.loads(zlib.decompress(base64.b64decode(e)))
        yield kic, quarter, uri, time, flux, fluxerr


if __name__ == '__main__':
    # input comes from STDIN (standard input)
    data = read_mapper_output(sys.stdin)

    # groupby groups multiple quarters together for each Kepler ID
    #   current_kic is current Kepler ID
    #   group - iterator yielding all ["&lt;current_word&gt;", "&lt;count&gt;"] items

    for current_kic, group in groupby(data, itemgetter(0)):
        try:
            all_quarters = [[q, time, flux, eflux] for _, q, _, time, flux, eflux in group]
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

