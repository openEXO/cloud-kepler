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
        self.prihdr = None
        self.prihdu = None
        self.cfghdu = None
        self.ext_list = []


    def make_header(self, kic_cadence_id):
        '''
        Create the FITS header. Currently, only the KIC ID of the relevant star
        is saved in this header, but other fields will be added later.

        :param kic_id: KIC ID of this star
        :type kic_id: str
        '''
        self.prihdr = pyfits.Header()
        kic_id, cadence = kic_cadence_id.split('_')
        self.prihdr['KIC_ID'] = kic_id
        self.prihdr['CADENCE'] = 'long' if cadence == 'llc' else 'short'


    def push_bls_output(self, bls_out, segstart, segend):
        '''
        Push the output from a single run of the BLS pulse algorithm onto
        a "stack". This way, the last run of the algorithm will appear first
        in the output FITS file.

        :param bls_out: Unprocessed output from ``bls_pulse_*``
        :type bls_out: dict
        :param segstart: Start time of segments
        :type segstart: np.ndarray
        :param segend: End time of segments
        :type segend: np.ndarray
        '''
        keys = bls_out.keys()
        vals = bls_out.values()
        columns = []

        columns.append(pyfits.Column(name='segstart', array=segstart,
            format='D'))
        columns.append(pyfits.Column(name='segend', array=segend, format='D'))

        for k, v in zip(keys, vals):
            columns.append(pyfits.Column(name=k, array=v, format='D'))

        cols = pyfits.ColDefs(columns)
        
        try:
            tbhdu = pyfits.BinTableHDU.from_columns(cols)
        except AttributeError:
            temp = pyfits.FITS_rec.from_columns(cols)
            tbhdu = pyfits.BinTableHDU(temp)

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
        hdr = pyfits.Header()

        if clean_out is not None:
            keys = clean_out.keys()
            vals = clean_out.values()

            for k, v in zip(keys, vals):
                hdr[k] = v

            try:
                hdr.comments['period'] = 'period of strongest signal [days]'
            except KeyError:
                pass

            try:
                hdr.comments['phase'] = 'phase of strongest periodic ' \
                    'signal [XXXXX]'
            except KeyError:
                pass

            try:
                hdr.comments['duration'] = 'duration of strongest ' \
                    'periodic signal [days]'
            except KeyError:
                pass

            try:
                hdr.comments['depth'] = 'depth of strongest periodic signal'
            except KeyError:
                pass

        columns = [pyfits.Column(name='Time', array=time, format='D',
            unit='BJD - 2454833'),
            pyfits.Column(name='Flux', array=flux, format='D'),
            pyfits.Column(name='Flux error', array=fluxerr, format='D')]
        cols = pyfits.ColDefs(columns)

        try:
            tbhdu = pyfits.BinTableHDU.from_columns(cols, header=hdr)
        except AttributeError:
            temp = pyfits.FITS_rec.from_columns(cols)
            tbhdu = pyfits.BinTableHDU(temp, header=hdr)        

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

        hdr = pyfits.Header()
        hdr['EXTNAME'] = 'INPUT_PARAMS'

        try:
            self.cfghdu = pyfits.TableHDU.from_columns(cols, header=hdr)
        except AttributeError:
            temp = pyfits.FITS_rec.from_columns(cols)
            self.cfghdu = pyfits.TableHDU(temp, header=hdr)


    def write_file(self, fname, clobber=False):
        '''
        Write all the data stored internally in this object to a file on disk.

        :param fname: The name of the file to save
        :type fname: str
        :param clobber: Whether to clobber an existing output file; passed
            directly to pyfits
        :type clobber: bool
        '''
        hdus = []

        if self.prihdr is not None:
            self.prihdr['N_EXTEN'] = (len(self.ext_list) + 1,
                '(n_passes * 2) + 1')
            self.prihdu = pyfits.PrimaryHDU(header=self.prihdr)
            hdus.append(self.prihdu)

        if len(self.ext_list) > 0:
            j = len(self.ext_list) / 2

            for i in xrange(0,len(self.ext_list),2):
                self.ext_list[i].header['EXTNAME'] = 'BLIP-DIP_Pass_%02d' % j
                self.ext_list[i+1].header['EXTNAME'] = 'TIME-FLUX_Pass_%02d' % j

                j -= 1

            hdus.extend(self.ext_list)

        if self.cfghdu is not None:
            hdus.append(self.cfghdu)

        hdulist = pyfits.HDUList(hdus)
        hdulist.writeto(fname, clobber=clobber)

