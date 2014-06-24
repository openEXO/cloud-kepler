#!/usr/bin/env python
"""Kepler FITS retrieval.  This module will retrieve Kepler lightcurve FITS files based on
a specified source.  It defines a class called LC_Stream that stores the relevant lightcurve
data for one-or-many Kepler targets and one-or-many Quarters as a 64-bit encoded string to be
passed along to other modules directly through memory.
Reference: http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/
"""

############################################################################################
## Place import commands and logging options.
############################################################################################
import sys
import os
import logging
import urllib2
import tempfile
from contextlib import contextmanager
import pyfits
import base64
import numpy as np
from zlib import compress, decompress
import json
from argparse import ArgumentParser
############################################################################################


############################################################################################
# Define the possible timestamps in the filename for a given Quarter as a global constant.
# This allows the software to determine what Quarter a given file came from without having 
# to read the FITS header (since these timestamps are in the file name).
# NOTE:  Have to add Q17 timestamp here.
# NOTE:  There are two possible quarter prefixes for Quarter 4 data files.  The more common 
# one is put first so that it is checked before the rarer one.
# NOTE:  This list assumes long-cadence data ONLY.
############################################################################################
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
                    '16': "2013098041711",
                    '17': "2013131215648"}
############################################################################################


############################################################################################
# This class defines a generic Exception to use for errors raised in this module.
############################################################################################
class GetDataError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
############################################################################################


############################################################################################
# Define a class called "LC_Stream", a.k.a., lightcurve stream.  It is created out of data 
# read from Kepler FITS files, and is passed along as a single 64-bit string.  The optional 
# fits_stream parameter should be a numpy array containing the times, fluxes, and flux 
# errors read from a FITS file.
############################################################################################
class LC_Stream:
    def __init__(self, fits_stream=None):
        '''
        Default the data stream to be an empty string; otherwise, use the contents of
        `fits_stream`, which should be a NumPy array.
        '''
        if fits_stream is None:
            self.datastream = ""
        else:
            self.datastream = base64.b64encode(compress(json.dumps(fits_stream.tolist())))


    def pprint(self):
        '''
        Prints the data stream to the screen in a human-readable format.
        '''
        flux_array = json.loads(decompress(base64.b64decode(self.datastream)))
        for dataelem in flux_array: 
            print '{0: <11.5f} {1: <15.5f} {2: <7.5f}'.format(dataelem[0], dataelem[1], dataelem[2])
############################################################################################


############################################################################################
# This function, and its utility functions, retrieves data from the MAST archive over the web.
############################################################################################
def get_data_from_mast(data):
    for kepler_id, quarter in data:
        try:
            # Create variable that will be the key to use in the QUARTER_PREFIXES dictionary.
            # The backup path is only defined if it's Quarter 4.
            quarter_key = quarter
            path_backup = ""

            # Special handling required since there are two Quarter 4 timestamps possible.
            # First start off with Quarter 4a.
            if quarter == '4':
                quarter_key = '4a'

            # Fix kepler_id missing zero-padding
            if len(kepler_id) < 9:
                kepler_id = str("%09d" % int(kepler_id))            

            # Now create the URL regardless of Quarter.
            path = get_mast_path(kepler_id, quarter_key)

            # If Quarter 4, prepare a "backup" path of the second possible epoch in Quarter 4.
            if quarter == '4':
                quarter_key = '4b'
                path_backup = prepare_path(kepler_id, quarter_key)

            # Download the requested URL.
            fits_stream = download_file_serialize(path, path_backup)
            tempfile, this_lc_stream = process_fits_object(fits_stream)
            
            # Write the result to STDOUT as this will be an input to a
            # reducer that aggregates the querters together
            print "\t".join([kepler_id, quarter, path, this_lc_stream.datastream])
            os.unlink(tempfile)
        except:
            pass


def download_file_serialize(uri, uri_backup):
    '''
    Downloads the FITS file at the given URI; if that fails, attempts to download the
    file from the backup URI. On success, returns a raw character stream. On failure,
    output is an empty string.
    '''
    try:
        response = urllib2.urlopen(uri)
        fits_stream = response.read()
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


def get_mast_path(kepler_id, quarter):
    '''
    Construct download path from MAST, given the Kepler ID and quarter.
    '''
    prefix = kepler_id[0:4]
    path = "http://archive.stsci.edu/pub/kepler/lightcurves/" + prefix + "/" + kepler_id + \
        "/kplr" + kepler_id + "-" + QUARTER_PREFIXES[quarter] + "_llc.fits"
    
    return path


def process_fits_object(fits_string):
    '''
    Process FITS file object and extract info.
    http://stackoverflow.com/questions/11892623/python-stringio-and-compatibility-with-with-statement-context-manager
    Returns the temporary file name and LC_Stream object.
    '''
    test = ""
    with tempinput(fits_string) as tempfilename:
        test = tempfilename
        fitsdata = pyfits.getdata(tempfilename)
        bjd_trunci = float(pyfits.getval(tempfilename, "bjdrefi", ext=1))
        bjd_truncf = float(pyfits.getval(tempfilename, "bjdreff", ext=1))
        # Note: Times are updated to be in proper reduced barycentric Julian date, 
        # RBJD = BJD - 2400000.0
        time = fitsdata['TIME'] + bjd_trunci + bjd_truncf - 2400000.
        pdcflux = fitsdata['PDCSAP_FLUX']
        pdcerror = fitsdata['PDCSAP_FLUX_ERR']
        errorstat = fitsdata['SAP_QUALITY']
        time_pdcflux_pdcerror = np.column_stack((time, pdcflux, pdcerror))

        ndx = np.where(errorstat == 0)
        retval = LC_Stream(time_pdcflux_pdcerror[ndx])
        
        # Fix for windows, returns the filename into main so that os.unlink can be called there
        return test, retval


@contextmanager
def tempinput(data):
    """
    Handle old legacy code that absolutely demands a filename instead of streaming file content.
    """
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(data)
    temp.close()
    yield temp.name
############################################################################################


############################################################################################
# This function, and its utility functions, retrieves data from a disk given a specified 
# root directory.The FITS files are expected to be under that directory in the following 
# format: <root directory>/<4-digit short KepID>/<full KepID>/
############################################################################################
def get_data_from_disk(data, datapath):
    for kepler_id, quarter in data:
        try:
            # Create variable that will be the key to use in the QUARTER_PREFIXES dictionary.  
            # The backup path is only defined if it's Quarter 4.
            quarter_key = quarter
            path_backup = ""

            # Special handling required since there are two Quarter 4 timestamps possible.  
            # First start off with Quarter 4a.
            if quarter == '4':
                quarter_key = '4a'

            # Fix kepler_id missing zero-padding
            if len(kepler_id) < 9:
                kepler_id = str("%09d" % int(kepler_id))            

            # Now create the URL regardless of Quarter.
            path = get_fits_path(datapath, kepler_id, quarter_key)

            # If Quarter 4, prepare a "backup" path of the second possible epoch in Quarter 4.
            if quarter == '4':
                quarter_key = '4b'
                path_backup = get_fits_path(datapath, kepler_id, quarter_key)

            # Read in the FITS file and create the LC_Stream object.
            this_lc_stream = read_fits_file(path, kepler_id, path_backup)
            
            # Write the result to STDOUT as this will be an input to a
            # reducer that aggregates the querters together
            print "\t".join([kepler_id, quarter, path, this_lc_stream.datastream])
        except:
            pass


def get_fits_path(datapath, kepler_id, quarter):
    "Construct file path on disk, given the base path, Kepler ID, and quarter."
    prefix = kepler_id[0:4]
    # Changed to os.path.join for more flexibility with `datapath` syntax
    path = os.path.join(datapath, prefix, kepler_id, 'kplr' + kepler_id + '-' + 
        QUARTER_PREFIXES[quarter] + '_llc.fits')
    
    return path


def read_fits_file(input_fits_file, kepler_id, input_fits_file_backup):
    """"
    Read FITS file from disk for each quarter and each object into memory.
    """
    try:
        hdulist = pyfits.open(input_fits_file)
    except:
         # If the first file path failed (usually because there are alternative timestamps in 
         # the file names), try the backup file name.
        if input_fits_file_backup != "":
            try:
                hdulist = pyfits.open(input_fits_file_backup)
            except:
                logging.error("Cannot read: " + input_fits_file + " or " + input_fits_file_backup)
                # Return an empty LC_Stream object in this case...
                return LC_Stream()
        else:
            logging.error("Cannot read: "+ input_fits_file)
            # Return an empty LC_Stream object in this case...
            return LC_Stream()

    # Otherwise we've successfully opened the FITS file, so read the data, close the FITS 
    # file, and create the LC_Stream object.
    # Note: Times are updated to be in proper reduced barycentric Julian date, 
    # RBJD = BJD - 2400000.0
    fitsdata = hdulist[1].data
    bjd_trunci = float(hdulist[1].header['bjdrefi'])
    bjd_truncf = float(hdulist[1].header['bjdreff'])
    time = fitsdata['TIME'] + bjd_trunci + bjd_truncf - 2400000.
    pdcflux = fitsdata['PDCSAP_FLUX']
    pdcerror = fitsdata['PDCSAP_FLUX_ERR']
    errorstat = fitsdata['SAP_QUALITY']
    time_pdcflux_pdcerror = np.column_stack((time, pdcflux, pdcerror))

    ndx = np.where(errorstat == 0)
    retval = LC_Stream(time_pdcflux_pdcerror[ndx])
    hdulist.close()

    return retval
############################################################################################


############################################################################################
# This code block contains the main function, and utility functions only called within "main".
# The input "source" is a scalar string set via the command line that specifies from where 
# the data should be retrieved.
#
# Example: more <text file containing Kepler IDs and Quarters> | python get_data.py mast
############################################################################################
def main(source,datapath):
    """"
    Read KIC IDs and quarters from STDIN, retrieve FITS files, and
    process FITS file on the fly in memory.
    """  
    # Read in a list of KIC IDs and Quarter numbers to process from STDIN.
    data = read_input(sys.stdin)

    # Call the correct function based on the desired source.
    if source == "mast":
        get_data_from_mast(data)
    elif source == "disk":
        get_data_from_disk(data,datapath)
    else:
        raise GetDataError("Invalid choice for source parameter.")


def read_input(file):
    for line in file:
        # Split the line into words
        s = line.split()

        # Only yield if this was a valid line (allows for blank lines in STDIN)
        if len(s) == 2:
            yield s
############################################################################################

if __name__ == "__main__":
    parser = ArgumentParser(description="Retrieve Kepler lightcurve data given a set of Kepler "
        "IDs and Quarter numbers from STDIN.")
    parser.add_argument("source", action="store", choices=['mast','disk'], 
        help="Select the source where Kepler FITS files should be retrieved.")
    parser.add_argument("datapath", action="store", nargs='?', default=os.curdir+os.sep, 
        help="(Root) path to the Kepler lightcurve data, such that root is the path part "
            "<root>/<nnnn>/<nnnnnnnnn>/.  Defaults to the current working directory.")
    args = parser.parse_args()
    
    # Note: The trailing separator is not necessary anymore because of os.path.join modification
    main(args.source, os.path.normpath(args.datapath))

