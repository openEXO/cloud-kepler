#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Kepler FITS retrieval.  This module will retrieve Kepler lightcurve FITS files based on
a specified source.  It defines a class called DataStream that stores the relevant lightcurve
data for one-or-many Kepler targets and one-or-many Quarters as a 64-bit encoded string to be
passed along to other modules directly through memory.
Reference: http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/
'''

import sys
import os
import logging
import urllib2
import tempfile
import pyfits
import numpy as np
from contextlib import contextmanager
from argparse import ArgumentParser
from utils import encode_array

# Basic logging configuration.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


############################################################################################
# Define the possible timestamps in the filename for a given Quarter as a global constant.
# This allows the software to determine what Quarter a given file came from without having
# to read the FITS header (since these timestamps are in the file name).
############################################################################################
NUM_QUARTERS = 17

LONG_QUARTER_PREFIXES = {'0':['2009131105131'],
                         '1':['2009166043257'],
                         '2':['2009259160929'],
                         '3':['2009350155506'],
                         '4':['2010078095331','2010009091648'],
                         '5':['2010174085026'],
                         '6':['2010265121752'],
                         '7':['2010355172524'],
                         '8':['2011073133259'],
                         '9':['2011177032512'],
                         '10':['2011271113734'],
                         '11':['2012004120508'],
                         '12':['2012088054726'],
                         '13':['2012179063303'],
                         '14':['2012277125453'],
                         '15':['2013011073258'],
                         '16':['2013098041711'],
                         '17':['2013131215648']}

SHORT_QUARTER_PREFIXES = {'0':['2009131110544'],
                          '1':['2009166044711'],
                          '2':['2009201121230','2009231120729','2009259162342'],
                          '3':['2009291181958','2009322144938','2009350160919'],
                          '4':['2010009094841','2010019161129','2010049094358','2010078100744'],
                          '5':['2010111051353','2010140023957','2010174090439'],
                          '6':['2010203174610','2010234115140','2010265121752'],
                          '7':['2010296114515','2010326094124','2010355172524'],
                          '8':['2011024051157','2011053090032','2011073133259'],
                          '9':['2011116030358','2011145075126','2011177032512'],
                          '10':['2011208035123','2011240104155','2011271113734'],
                          '11':['2011303113607','2011334093404','2012004120508'],
                          '12':['2012032013838','2012060035710','2012088054726'],
                          '13':['2012121044856','2012151031540','2012179063303'],
                          '14':['2012211050319','2012242122129','2012277125453'],
                          '15':['2012310112549','2012341132017','2013011073258'],
                          '16':['2013017113907','2013065031647','2013098041711'],
                          '17':['2013121191144','2013131215648']}
############################################################################################


class DataStream:
    '''
    This class is a wrapper for a string of time, flux, and flux error.
    '''

    def __init__(self, arrays=None):
        '''
        Default the data stream to be an empty string; otherwise, use the contents of
        `fits_stream`, which should be a NumPy array.
        '''
        if arrays is None:
            self.dstream1 = ''
            self.dstream2 = ''
            self.dstream3 = ''
        else:
            time, flux, fluxerr = arrays
            self.dstream1 = encode_array(time)
            self.dstream2 = encode_array(flux)
            self.dstream3 = encode_array(fluxerr)


    def pprint(self):
        '''
        Prints the data stream to the screen in a human-readable format.
        '''
        time = decode_array(self.dstream1)
        flux = decode_array(self.dstream2)
        fluxerr = decode_array(self.dstream3)

        for d1, d2, d3 in zip(time, flux, fluxerr):
            print '{0: <11.5f} {1: <15.5f} {2: <7.5f}'.format(d1, d2, d3)


############################################################################################
# This function, and its utility functions, retrieves data from the MAST archive over the web.
############################################################################################
def get_data_from_mast(data):
    for kepler_id, quarter, suffix in data:
        # Fix kepler_id missing zero-padding
        if len(kepler_id) < 9:
            kepler_id = str("%09d" % int(kepler_id))

        # Now create the URLs.
        path = get_mast_path(kepler_id, quarter, suffix)

        for p in path:
            # Download the requested URL.
            try:
                fits_stream = download_file_serialize(p)
                tempfile, stream = process_fits_object(fits_stream)
            except RuntimeError:
                logging.error('Cannot download: ' + p)
                continue

            # Write the result to STDOUT as this will be an input to a
            # reducer that aggregates the querters together
            print "\t".join([kepler_id, quarter, p, stream.dstream1, stream.dstream2,
                stream.dstream3])
            os.unlink(tempfile)


def download_file_serialize(uri):
    '''
    Downloads the FITS file at the given URI; if that fails, attempts to download the
    file from the backup URI. On success, returns a raw character stream. On failure,
    output is an empty string.
    '''
    try:
        response = urllib2.urlopen(uri)
        fits_stream = response.read()
    except:
        raise RuntimeError

    return fits_stream


def get_mast_path(kepler_id, quarter, suffix):
    '''
    Construct download path from MAST, given the Kepler ID and quarter.
    '''
    prefix = kepler_id[0:4]
    path = []

    if suffix == 'llc':
        for p in LONG_QUARTER_PREFIXES[quarter]:
            path.append('http://archive.stsci.edu/pub/kepler/lightcurves/' + prefix + '/' + \
                kepler_id + '/kplr' + kepler_id + '-' + p + '_' + suffix + '.fits')
    elif suffix == 'slc':
        for p in SHORT_QUARTER_PREFIXES[quarter]:
            path.append('http://archive.stsci.edu/pub/kepler/lightcurves/' + prefix + '/' + \
                kepler_id + '/kplr' + kepler_id + '-' + p + '_' + suffix + '.fits')
    else:
        raise ValueError('Invalid cadence key: %s' % suffix)

    return path


def process_fits_object(fits_string):
    '''
    Process FITS file object and extract info.
    http://stackoverflow.com/questions/11892623/python-stringio-and-compatibility-with-with-statement-context-manager
    Returns the temporary file name and DataStream object.
    '''
    test = ''
    with tempinput(fits_string) as tempfilename:
        test = tempfilename
        fitsdata = pyfits.getdata(tempfilename)
        bjd_trunci = float(pyfits.getval(tempfilename, 'bjdrefi', ext=1))
        bjd_truncf = float(pyfits.getval(tempfilename, 'bjdreff', ext=1))

        # Note: Times are updated to be in proper reduced barycentric Julian date,
        # RBJD = BJD - 2400000.0
        time = fitsdata['TIME'] + bjd_trunci + bjd_truncf - 2400000.
        pdcflux = fitsdata['PDCSAP_FLUX']
        pdcerror = fitsdata['PDCSAP_FLUX_ERR']
        errorstat = fitsdata['SAP_QUALITY']

        ndx = np.where(errorstat == 0)
        retval = DataStream(arrays=(time[ndx], pdcflux[ndx], pdcerror[ndx]))

        # Fix for windows, returns the filename into main so that os.unlink can be called there
        return test, retval


@contextmanager
def tempinput(data):
    '''
    Handle old legacy code that absolutely demands a filename instead of streaming file content.
    '''
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
    for kepler_id, quarter, suffix in data:
        # Fix kepler_id missing zero-padding
        if len(kepler_id) < 9:
            kepler_id = str("%09d" % int(kepler_id))

        # Now create the URL regardless of Quarter.
        path = get_fits_path(datapath, kepler_id, quarter, suffix)

        for p in path:
            # Read in the FITS file and create the DataStream object.
            try:
                stream = read_fits_file(p, kepler_id)
            except RuntimeError:
                logging.error("Cannot read: "+ input_fits_file)
                continue

            # Write the result to STDOUT as this will be an input to a
            # reducer that aggregates the querters together
            print "\t".join([kepler_id, quarter, p, stream.dstream1, stream.dstream2,
                stream.dstream3])


def get_fits_path(datapath, kepler_id, quarter, suffix):
    '''
    Construct file path on disk, given the base path, Kepler ID, and quarter.
    '''
    prefix = kepler_id[0:4]
    path = []

    if suffix == 'llc':
        for p in LONG_QUARTER_PREFIXES[quarter]:
            path.append(os.path.join(datapath, prefix, kepler_id, 'kplr' + kepler_id + '-' +
                p + '_' + suffix + '.fits'))
    elif suffix == 'slc':
        for p in SHORT_QUARTER_PREFIXES[quarter]:
            path.append(os.path.join(datapath, prefix, kepler_id, 'kplr' + kepler_id + '-' +
                p + '_' + suffix + '.fits'))
    else:
        raise ValueError('Invalid cadence key: %s' % suffix)

    return path


def read_fits_file(input_fits_file, kepler_id):
    '''
    Read FITS file from disk for each quarter and each object into memory.
    '''
    try:
        hdulist = pyfits.open(input_fits_file)
    except:
        raise RuntimeError

    # Otherwise we've successfully opened the FITS file, so read the data, close the FITS
    # file, and create the DataStream object.
    # Note: Times are updated to be in proper reduced barycentric Julian date,
    # RBJD = BJD - 2400000.0
    fitsdata = hdulist[1].data
    bjd_trunci = float(hdulist[1].header['bjdrefi'])
    bjd_truncf = float(hdulist[1].header['bjdreff'])
    time = fitsdata['TIME'] + bjd_trunci + bjd_truncf - 2400000.
    pdcflux = fitsdata['PDCSAP_FLUX']
    pdcerror = fitsdata['PDCSAP_FLUX_ERR']
    errorstat = fitsdata['SAP_QUALITY']

    ndx = np.where(errorstat == 0)
    retval = DataStream(arrays=(time[ndx], pdcflux[ndx], pdcerror[ndx]))
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
        raise ValueError("Invalid choice for source parameter.")


def read_input(file):
    for line in file:
        # Split the line into words
        s = line.split()

        # Only yield if this was a valid line (allows for blank lines in STDIN)
        if len(s) == 3:
            if s[1] == '*':
                for i in xrange(NUM_QUARTERS):
                    yield [s[0], str(i), s[2]]
            else:
                yield s
############################################################################################

if __name__ == "__main__":
    # Set up the command line argument parser.
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

