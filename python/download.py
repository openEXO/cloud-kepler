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

# NOTE:  There are two possible quarter prefixes for Quarter 4 data files.  The more common one is put first so that it is checked before the rarer one.
# NOTE:  This list assumes long-cadence data ONLY.
QUARTER_PREFIXES = {'0':  "2009131105131",
                    '1':  "2009166043257",
                    '2':  "2009259160929",
                    '3':  "2009350155506",
                    '4a':  "2010078095331",
                    '4b':  "2010009091648",
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
                    '15': "2013011073258",
                    '16': "2013098041711"}

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

def process_fits_object(fits_string):
    """
    Process FITS file object and extract info.
    http://stackoverflow.com/questions/11892623/python-stringio-and-compatibility-with-with-statement-context-manager
    """
    test = ""
    with tempinput(fits_string) as tempfilename:
        test = tempfilename
        fits_list = pyfits.getdata(tempfilename)
        error_status = np.asarray([c[9] for c in fits_list])
        bjd_trunci = float(pyfits.getval(tempfilename, "bjdrefi", ext=1))
        bjd_truncf = pyfits.getval(tempfilename, "bjdreff", ext=1)
        ## Note: Times are updated to be in proper reduced barycentric Julian date, RBJD = BJD - 2400000.0
        time_pdcflux_pdcerror = np.asarray(
            [[c[0]+bjd_trunci+bjd_truncf-2400000.0,c[7],c[8]] for i,c in
             enumerate(fits_list) if error_status[i] == 0])
        retval = base64.b64encode(compress(simplejson.dumps(time_pdcflux_pdcerror.tolist())))
        #fix for windows, returns the filename into main so that os.unlink can be called there
        #props go to the swag STScI IT guy for figuring this out.
        #I'll add his name here once I work up the courage to ask him.
        return test, retval
        
def download_file_serialize(uri, kepler_id, uri_backup):
    """"
    Download FITS file for each quarter for each object into memory and read FITS file.
    """
    try:
        response = urllib2.urlopen(uri)
        fits_stream = response.read()
        #Write file object (but do not save to a local file)
    except:
        # If the first uri failed, try the backup uri.
        if uri_backup != "":
            try:
                response = urllib2.urlopen(uri_backup)
                fits_stream = response.read()
            except:
                logging.error("Cannot download: " + uri + " or " + uri_backup)
                fits_stream = ""
        else:
            logging.error("Cannot download: "+ uri)
            fits_stream = ""
    return fits_stream

def prepare_path(kepler_id,quarter):
    "Construct download path from MAST."
    prefix = kepler_id[0:4]
    path = "http://archive.stsci.edu/pub/kepler/lightcurves/"+\
        prefix+"/"+kepler_id+"/kplr"+kepler_id+"-"+QUARTER_PREFIXES[quarter]+"_llc.fits"
    return path

def main(separator="\t"):
    """"
    Read from KICs and quarters from STDIN, download FITS files and
    process FITS file on the fly in memory.
    """
    data = read_input(sys.stdin)
    for kepler_id, quarter in data:
        try:
            # Create variable that will be the key to use in the QUARTER_PREFIXES dictionary.  The backup path is only defined if it's Quarter 4.
            quarter_key = quarter
            path_backup = ""

            # Special handling required since there are two Quarter 4 timestamps possible.  First start off with Quarter 4a.
            if quarter == '4':
                quarter_key = '4a'
            
            # Fix kepler_id missing zero-padding
            if len(kepler_id) < 9:
                kepler_id = str("%09d" % int(kepler_id))

            # Now create the URL regardless of Quarter.
            path = prepare_path(kepler_id, quarter_key)

            # If Quarter 4, prepare a "backup" path of the second possible epoch in Quarter 4.
            if quarter == '4':
                quarter_key = '4b'
                path_backup = prepare_path(kepler_id, quarter_key)

            # Download the requested URL.
            #fits_stream = download_file_serialize(path, kepler_id, path_backup)
            # load locally
            fits_stream = open("../../data/kplr"+kepler_id+"-"+QUARTER_PREFIXES[quarter_key]+"_llc.fits", "rb").read()
            tempfile, fits_array_string = process_fits_object(fits_stream)
            # Write the result to STDOUT as this will be an input to a
            # reducer that aggregates the querters together
            print "\t".join([kepler_id, quarter, path, fits_array_string])
            os.unlink(tempfile)

        except:
            pass

if __name__ == "__main__":
    main()
