# -*- coding: utf-8 -*-

import pyfits
import numpy as np


class BLSFitsBundler():
    '''
    Bundles all output from BLS pulse pipeline into a single FITS
    file and saves it to disk.
    '''

    def __init__(self):
        self.prihdu = None
        self.cfghdu = None
        self.ext_list = []


    def make_header(self, kic_id):
        prihdr = pyfits.Header()
        prihdr['KIC_ID'] = kic_id
        self.prihdu = pyfits.PrimaryHDU(header=prihdr)


    def push_bls_output(self, bls_out):
        keys = bls_out.keys()
        vals = bls_out.values()
        columns = []

        for k, v in zip(keys, vals):
            columns.append(pyfits.Column(name=k, array=v, format='D'))

        cols = pyfits.ColDefs(columns)
        tbhdu = pyfits.BinTableHDU.from_columns(cols)
        self.ext_list.insert(0, tbhdu)


    def push_detrended_lightcurve(self, time, flux, fluxerr, clean_out=None):
        if clean_out is not None:
            hdr = pyfits.Header()
            keys = clean_out.keys()
            vals = clean_out.values()

            for k, v in zip(keys, vals):
                hdr[k] = v

        columns = [pyfits.Column(name='Time', array=time, format='D'),
            pyfits.Column(name='Flux', array=flux, format='D'),
            pyfits.Column(name='Flux error', array=fluxerr, format='D')]
        cols = pyfits.ColDefs(columns)
        tbhdu = pyfits.BinTableHDU.from_columns(cols)
        self.ext_list.insert(0, tbhdu)


    def push_config(self, config):
        keys = config.keys()
        vals = config.values()

        columns = [pyfits.Column(name='Parameter', array=keys, format='A20'),
            pyfits.Column(name='Value', array=vals, format='A20')]
        cols = pyfits.ColDefs(columns)
        self.cfghdu = pyfits.TableHDU.from_columns(cols)


    def write_file(self, fname):
        if self.prihdu is not None:
            hdus = [self.prihdu]

        if len(self.ext_list) > 0:
            hdus.extend(self.ext_list)

        if self.cfghdu is not None:
            hdus.append(self.cfghdu)

        hdulist = pyfits.HDUList(hdus)
        hdulist.writeto(fname)

