#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pyfits
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from argparse import ArgumentParser
from utils import setup_logging

# Basic logging configuration.
logger = setup_logging(__file__)


def __init_parser():
    '''
    Set up an argument parser for all possible command line options. Returns
    the parser object.

    :rtype: argparse.ArgumentParser
    '''
    parser = ArgumentParser()
    parser.add_argument('infile', action='store', type=str,
        help='FITS file written by BLS pulse algorithm')
    parser.add_argument('-o', '--outfile', action='store', type=str,
        default='', help='[Optional] Name of the output file to write; default is '
            'same as input file with PDF extension.')

    return parser


# Read in and parse all command line arguments.
parser = __init_parser()
args = parser.parse_args()
infile = args.infile

if args.outfile == '':
    outfile = os.path.join(os.path.dirname(infile),
        '.'.join(os.path.basename(infile).split('.')[:-1]) + '.pdf')
else:
    outfile = args.outfile

logger.info('Saving output to file ' + outfile)


# Open the input FITS file and extract the HDUs.
hdulist = pyfits.open(infile)
kic_id = hdulist[0].header['kic_id']
data_hdus = hdulist[1:-1]


# Based on the tutorial/example at:
# matplotlib.org/examples/pylab_examples/multipage_pdf.html

# Create the PdfPages object to which we will save the pages:
# The with statement makes sure that the PdfPages object is closed
# properly at the end of the block, even if an Exception occurs.
with PdfPages(outfile) as pdf:
    for i in xrange(0, len(data_hdus), 2):
        bls = data_hdus[i].data
        lc = data_hdus[i+1].data
        lchdr = data_hdus[i+1].header

        # Extract the light curve.
        time = lc['time']
        flux = lc['flux']

        try:
            period = lchdr['period']
            phase = lchdr['phase']
            duration = lchdr['duration']

            pftime = np.mod(time, period)
            signal_mask = ((pftime > phase - 0.5 * duration) & (pftime < phase + 0.5 * duration))

            plt.subplot(211)
            plt.scatter(time, flux, color='blue')

            plt.subplot(212)
            plt.scatter(pftime[~signal_mask], flux[~signal_mask], color='blue')
            plt.scatter(pftime[signal_mask], flux[signal_mask], color='green')
        except KeyError:
            plt.subplot(111)
            plt.scatter(time, flux, color='blue')

            pass

        pdf.savefig()
        plt.close()

