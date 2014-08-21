# -*- coding: utf-8 -*-

import pyfits
import numpy as np


class BLSOutput():
    def __init__(self, fname):
        self.hdulist = pyfits.open(fname)


    def __getattr__(self, name):
        if name.lower() == 'dipblips':
            return [np.array(db.data) for db in self.hdulist[1:-1:2]]
        elif name.lower() == 'lightcurves':
            return [np.array(lc.data) for lc in self.hdulist[2:-1:2]]
        elif name.lower() == 'params':
            return dict(self.hdulist[-1].data)
        elif name.lower() == 'num_passes':
            return (int(self.hdulist[0].header['N_EXTEN']) - 1) / 2
        elif name.lower() == 'kic':
            return self.hdulist[0].header['KIC_ID']
        else:
            raise AttributeError('No such member')


    def __del__(self):
        try:
            self.hdulist.close()
        except AttributeError, OSError:
            pass

