#!/usr/bin/env python
"""
Perform Box Least Squares transit search according to the metodology of 
Kovacs, G., Zucker, S., & Mazeh, T. (2002) as adapted for Python by 
Still, M., & Barclay, T. (2012).
This code is a free adaptation of the PyKE library:
http://keplergo.arc.nasa.gov/PyKE.shtml
"""

import numpy as np


def read_mapper_output(file, separator='\t'):
    for line in file:
        kic, quarters,  flux_string = line.rstrip().split(separator)
        fits_array = simplejson.loads((decompress(base64.b64decode(flux_string))))
        yield kic, quarters, fits_array

if __name__ == "__main__":
    main()

