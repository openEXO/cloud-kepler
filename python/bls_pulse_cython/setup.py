# -*- coding: utf-8 -*-

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

import numpy as np

setup(cmdclass = {'build_ext': build_ext}, ext_modules =
    [Extension('bls_pulse_cython', sources=['bls_pulse_cython.pyx','bls_pulse_extern.c'],
    include_dirs=[np.get_include()])])

