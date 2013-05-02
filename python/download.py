#!/usr/bin/env python
"""An initial stab at a Kepler FITS downloader:
   http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/"""
import sys
import logging
import urllib2


QUARTER_PREFIXES = {'0':  "2010265121752",
                    '1':  "2009166043257",
                    '2':  "2009259160929",
                    '3':  "2009350155506",
                    '4':  "2010078095331",
                    '5':  "2010174085026",
                    '6':  "2010265121752",
                    '7':  "2010355172524",
                    '8':  "2011073133259",
                    '9':  "2011177032512",
                    '10': "2011271113734",
                    '11': "2012004120508",
                    '12': "2012088054726",
                    '13': "2012179063303",
                    '14': "2012277125453",
                    '15': "2013011073258",}

def read_input(file):
    for line in file:
        # split the line into words
        yield line.split()

def download_file_serialize(uri, kepler_id, quarter):
    "Download FITS file for each quarter for each object into memory and read FITS file"
    logging.info("Downloading: "+uri, level=logging.DEBUG)
    try:
        response = urllib2.urlopen(uri)
        fits = response.read()
    except:
        logging.error("Cannot download: "+ uri)
        fits = ""
    return fits

def prepare_path(kepler_id,quarter):
    prefix = kepler_id[0:4]
    path = "http://archive.stsci.edu/pub/kepler/lightcurves/"+\
        prefix+"/"+kepler_id+"/kplr"+kepler_id+"-"+QUARTER_PREFIXES[quarter]+"_llc.fits"
    return path

def main(separator="\t"):
    data = read_input(sys.stdin)
    for kepler_id, quarter in data:
        path = prepare_path(kepler_id, quarter)
        fits_stream = download_file_serialize(path, kepler_id, quarter)
        print kepler_id, quarter, path

if __name__ == "__main__":
    main()

        
