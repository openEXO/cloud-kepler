#!/usr/bin/env python
"""
A more advanced Reducer, using Python iterators and generators.
From http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/
"""

from itertools import groupby
from operator import itemgetter
import sys
import base64
import numpy as np
from zlib import decompress, compress
import simplejson

def read_mapper_output(file, separator='\t'):
    for line in file:
        kic, quarter, uri, fits_string = line.rstrip().split(separator)
        fits_array = simplejson.loads((decompress(base64.b64decode(fits_string))))
        yield kic, quarter, uri, fits_array


def encode_list(flux_list):
    return base64.b64encode(compress(simplejson.dumps(flux_list)))

def main(separator='\t'):
    # input comes from STDIN (standard input)
    data = read_mapper_output(sys.stdin, separator=separator)
    # groupby groups multiple quarters together for each Kepler ID
    #   current_kic is current Kepler ID
    #   group - iterator yielding all ["&lt;current_word&gt;", "&lt;count&gt;"] items
    concatenated_time_flux_eflux = list()
    for current_kic, group in groupby(data, itemgetter(0)):
        try:
            all_quarters = [[q, flux] for _, q, _, flux in group]
            concatenated_time_flux_eflux = list()
            for _, f in all_quarters:
                concatenated_time_flux_eflux.extend(f)
            all_q = [q for q,_ in all_quarters]
            print "%s%s%s%s%s" % (current_kic, separator, all_q, separator,
                                  encode_list(concatenated_time_flux_eflux))
        except ValueError:
            # count was not a number, so silently discard this item
            pass

if __name__ == "__main__":
    main()
