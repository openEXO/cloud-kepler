#!/usr/bin/env python
"""An initial stab at a Kepler FITS downloader:
   http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/"""
import sys
import argparse

QUARTER_PREFIXES = {'0': "something",
                    '1': "something",
                    '2': "something",}

def read_input(file):
    for line in file:
        # split the line into words
        yield line.split()

def main(separator="\t"):
    data = read_input(sys.stdin)
    for kepler_id, quarter in data:
        prefix = kepler_id[0:3]
        path = "http://archive.stsci.edu/pub/kepler/lightcurves/"+\
            prefix+"/"+kepler_id+"/kplr"+kepler_id+"-"+QUARTER_PREFIXES[quarter]+"_llc.fits"
        print kepler_id, quarter, path

if __name__ == "__main__":
    main()

        
