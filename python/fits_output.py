# -*- coding: utf-8 -*-

import pyfits
import numpy as np


class BLSFitsBundler():
    '''
    Bundles all output from BLS pulse pipeline into a single FITS file and saves
    it to disk. These files can be read by the ``postprocessing`` modules.
    '''

    def __init__(self):
        '''
        Initialize the object.
        '''
        self.prihdu = None
        self.cfghdu = None
        self.ext_list = []


    def make_header(self, kic_id):
        '''
        Create the FITS header. Currently, only the KIC ID of the relevant star
        is saved in this header, but other fields will be added later.

        :param kic_id: KIC ID of this star
        :type kic_id: str
        '''
        prihdr = pyfits.Header()
        prihdr['KIC_ID'] = kic_id
        self.prihdu = pyfits.PrimaryHDU(header=prihdr)


    def push_bls_output(self, bls_out):
        '''
        Push the output from a single run of the BLS pulse algorithm onto
        a "stack". This way, the last run of the algorithm will appear first
        in the output FITS file.

        :param bls_out: Unprocessed output from ``bls_pulse_*``
        :type bls_out: dict
        '''
        keys = bls_out.keys()
        vals = bls_out.values()
        columns = []

        for k, v in zip(keys, vals):
            columns.append(pyfits.Column(name=k, array=v, format='D'))

        cols = pyfits.ColDefs(columns)
        tbhdu = pyfits.BinTableHDU.from_columns(cols)
        self.ext_list.insert(0, tbhdu)


    def push_detrended_lightcurve(self, time, flux, fluxerr, clean_out=None):
        '''
        Push the output from the detrender onto a "stack". This way, the last
        lightcurve used will appear first in the FITS file.

        :param time: Vector of time observations
        :type time: np.ndarray
        :param flux: Vector of flux observations
        :type flux: np.ndarray
        :param fluxerr: Vector of errors on flux observations
        :type fluxerr: np.ndarray
        :param clean_out: Unprocessed output from ``clean_signal``
        :type clean_out: dict
        '''
        if clean_out is not None:
            hdr = pyfits.Header()
            keys = clean_out.keys()
            vals = clean_out.values()

            for k, v in zip(keys, vals):
                hdr[k] = v
        else:
            hdr = None

        columns = [pyfits.Column(name='Time', array=time, format='D'),
            pyfits.Column(name='Flux', array=flux, format='D'),
            pyfits.Column(name='Flux error', array=fluxerr, format='D')]
        cols = pyfits.ColDefs(columns)
        tbhdu = pyfits.BinTableHDU.from_columns(cols, header=hdr)
        self.ext_list.insert(0, tbhdu)


    def push_config(self, config):
        '''
        Push the configuration parameters onto a "stack". Note that this
        function should be called first so that configuration details appear
        last in the output FITS file!

        :param config: Configuration settings
        :type config: dict
        '''
        keys = config.keys()
        vals = config.values()

        columns = [pyfits.Column(name='Parameter', array=keys, format='A20'),
            pyfits.Column(name='Value', array=vals, format='A20')]
        cols = pyfits.ColDefs(columns)
        self.cfghdu = pyfits.TableHDU.from_columns(cols)


    def write_file(self, fname, clobber=False):
        '''
        Write all the data stored internally in this object to a file on disk.

        :param fname: The name of the file to save
        :type fname: str
        :param clobber: Whether to clobber an existing output file; passed directly to pyfits
        :type clobber: bool
        '''
        if self.prihdu is not None:
            hdus = [self.prihdu]

        if len(self.ext_list) > 0:
            hdus.extend(self.ext_list)

        if self.cfghdu is not None:
            hdus.append(self.cfghdu)

        hdulist = pyfits.HDUList(hdus)
        hdulist.writeto(fname, clobber=clobber)

