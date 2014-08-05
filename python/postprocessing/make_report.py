#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import Image
import pyfits
import cStringIO
import numpy as np

# Need this backend for running on remote systems.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, portrait
from reportlab.lib.units import inch, cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table
from argparse import ArgumentParser

sys.path.append(os.path.abspath(os.path.join(os.path.basename(__file__), '..')))
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
        default='', help='[Optional] Name of the output file to write; '
            'default is same as input file with PDF extension.')

    return parser


# Read in and parse all command line arguments.
parser = __init_parser()
args = parser.parse_args()
infile = args.infile

if args.outfile == '':
    basename = '.'.join(os.path.basename(infile).split('.')[:-1])
    outfile = os.path.join(os.path.dirname(infile), basename + '.pdf')
else:
    outfile = args.outfile

logger.info('Saving output to file ' + outfile)


# Open the input FITS file and extract the HDUs.
hdulist = pyfits.open(infile)
kic_id = hdulist[0].header['kic_id']
data_hdus = hdulist[1:-1]

c = canvas.Canvas(outfile)
page_width, page_height = portrait(letter)
c.setPageSize((page_width,page_height))

page_height /= inch
page_width /= inch
margin = 0.1
bigmargin = 0.25
fig_width = page_width - 2. * margin
fig_height = 0.5 * page_height - 2. * margin
color1 = 'CadetBlue'
color2 = 'Chartreuse'
alpha = 0.5
edgecolor = 'black'
markersize = 20

count = len(data_hdus) / 2

for i in xrange(0, len(data_hdus), 2):
    bls = data_hdus[i].data
    lc = data_hdus[i+1].data
    lchdr = data_hdus[i+1].header

    # Extract the light curve.
    time = lc['time']
    flux = lc['flux']
    yrng = np.ptp(flux)

    fig = plt.figure(figsize=(fig_width,fig_height), dpi=inch)

    try:
        period = lchdr['period']
        phase = lchdr['phase']
        duration = lchdr['duration']

        pftime = np.mod(time, period)
        signal_mask = ((pftime > phase - 0.5 * duration) &
            (pftime < phase + 0.5 * duration))

        plt.subplot(211)
        plt.scatter(time, flux, color=color1, edgecolor=edgecolor,
            alpha=alpha, s=markersize)
        plt.xlim(time[0], time[-1])
        plt.ylim(np.amin(flux) - 0.05 * yrng, np.amax(flux) + 0.05 * yrng)
        plt.xlabel(r'Time (BJD)')
        plt.ylabel(r'Flux')
        plt.title(r'KIC' + kic_id + r', pass #%d' % count)

        plt.subplot(212)
        plt.scatter(pftime[~signal_mask], flux[~signal_mask], color=color1,
            edgecolor=edgecolor, alpha=alpha, s=markersize)
        plt.scatter(pftime[signal_mask], flux[signal_mask],
            color=color2, edgecolor=edgecolor, alpha=alpha, s=markersize)
        plt.xlim(np.amin(pftime), np.amax(pftime))
        plt.ylim(np.amin(flux) - 0.05 * yrng, np.amax(flux) + 0.05 * yrng)
        plt.xlabel(r'Time (days)')
        plt.ylabel(r'Flux')
        plt.figtext(0.05, 0.02,
            r'P = %.4f, phi = %.2f' % (period, phase / period))
    except KeyError:
        plt.subplot(111)
        plt.scatter(time, flux, color=color1, edgecolor=edgecolor,
            alpha=alpha, s=markersize)
        plt.xlim(time[0], time[-1])
        plt.ylim(np.amin(flux) - 0.05 * yrng, np.amax(flux) + 0.05 * yrng)
        plt.xlabel(r'Time (BJD)')
        plt.ylabel(r'Flux')
        plt.title(r'KIC' + kic_id + r', pass #%d' % count)

    plt.tight_layout()

    imgdata = cStringIO.StringIO()
    fig.savefig(imgdata, format='png')
    imgdata.seek(0)
    img = ImageReader(imgdata)
    c.drawImage(img, margin * inch, 0.5 * page_height * inch,
        fig_width*inch, fig_height*inch)

    bls = np.array(bls, dtype=bls.dtype)

    ndx = np.argsort(-1. * bls['srsq_dip'])
    data = bls[ndx][0:15]
    data = data[['srsq_dip','duration_dip','depth_dip','midtime_dip']]
    data = data.tolist()
    data = map(lambda x: ('%.2e %.4f %.4f %.2f' % tuple(x)).split(), data)
    data.insert(0, ['Dip SR^2','Dip dur.','Dip depth','Dip mid.'])

    table = Table(data, colWidths=(inch,inch,inch,inch))
    w, h = table.wrapOn(c, page_width * inch, page_height * inch)
    table.drawOn(c, bigmargin * inch,
        0.5 * page_height * inch - h - bigmargin * inch)

    ndx = np.argsort(-1. * bls['srsq_blip'])
    data = bls[ndx][0:15]
    data = data[['srsq_blip','duration_blip','depth_blip','midtime_blip']]
    data = data.tolist()
    data = map(lambda x: ('%.2e %.4f %.4f %.2f' % tuple(x)).split(), data)
    data.insert(0, ['Blip SR^2','Blip dur.','Blip depth','Blip mid.'])

    table = Table(data, colWidths=(inch,inch,inch,inch))
    w, h = table.wrapOn(c, page_width * inch, page_height * inch)
    table.drawOn(c, page_width * inch - bigmargin * inch - w,
        0.5 * page_height * inch - h - bigmargin * inch)

    c.showPage()
    count -= 1

c.save()

