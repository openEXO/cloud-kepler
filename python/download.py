#!/usr/bin/env python
"""An initial stab at a Kepler FITS downloader:
   http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/"""
import sys
import os
import logging
import urllib2
import tempfile
from contextlib import contextmanager
import pyfits
import base64
import numpy as np
from zlib import compress
import simplejson

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

@contextmanager
def tempinput(data):
    """
    Handle old legacy code that absolutely demands a filename
    instead of streaming file content.
    """
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(data)
    temp.close()
    yield temp.name
    os.unlink(temp.name)

def process_fits_object(fits_string):
    """
    Process FITS file object and extract info.
    http://stackoverflow.com/questions/11892623/python-stringio-and-compatibility-with-with-statement-context-manager
    """

    with tempinput(fits_string) as tempfilename:
        fits_list = pyfits.getdata(tempfilename)
        error_status = np.asarray([c[9] for c in fits_list])
        time_pdcflux_pdcerror = np.asarray(
            [[c[0],c[7],c[8]] for i,c in
             enumerate(fits_list) if error_status[i] == 0])
    return base64.b64encode(compress(simplejson.dumps(time_pdcflux_pdcerror.tolist())))

def download_file_serialize(uri, kepler_id, quarter):
    """"
    Download FITS file for each quarter for each object into memory and read FITS file.
    """
    logging.warning("Downloading: KIC"+kepler_id+" quarter: "+quarter)
    try:
        response = urllib2.urlopen(uri)
        fits_stream = response.read()
        #Write file object (but do not save to a local file)
    except:
        logging.error("Cannot download: "+ uri)
        fits_stream = ""
    return fits_stream

def prepare_path(kepler_id,quarter):
    "Construct download path frm MAST."
    prefix = kepler_id[0:4]
    path = "http://archive.stsci.edu/pub/kepler/lightcurves/"+\
        prefix+"/"+kepler_id+"/kplr"+kepler_id+"-"+QUARTER_PREFIXES[quarter]+"_llc.fits"
    return path

def main(separator="\t"):
    """"
    Read from KICs and quarters from STDIN, download FITS files and
    process FITS file on the lfy in memory.
    """
    data = read_input(sys.stdin)
    for kepler_id, quarter in data:
        path = prepare_path(kepler_id, quarter)
        fits_stream = download_file_serialize(path, kepler_id, quarter)
        fits_array_string = process_fits_object(fits_stream)

        #Write the result to STDOUT as this will be an input to a
        #reducer that aggregates the querters together
        print "\t".join([kepler_id, quarter, path, fits_array_string])

if __name__ == "__main__":
    main()
