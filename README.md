Prototype of Cloud Kepler
=========================
| Master | v1.2 |
| :----: | :--: |
| ![Logo](https://travis-ci.org/openEXO/cloud-kepler.svg?branch=master) | ![Logo](https://travis-ci.org/openEXO/cloud-kepler.svg?branch=v1.2) |
| ![Logo](https://readthedocs.org/projects/cloud-kepler/badge/?version=latest) | ![Logo](https://readthedocs.org/projects/cloud-kepler/badge/?version=v1.2) |

Pipeline for processing Kepler lightcurves and search for signals of planets/flares.

More on the Kepler project:
* http://kepler.nasa.gov/

* http://keplergo.arc.nasa.gov/PyKE.shtml

More on Python Map-Reduce:
* http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/

More on Amazon Elastic Map-Reduce and Hadoop:
* http://aws.amazon.com/elasticmapreduce/

* http://hadoop.apache.org/


This branch includes a Cython implementation of the BLS algorithm. A few
things to keep in mind:

* Cython code must be compiled for changes to take effect. To compile, just run
  `make` from the Python base directory. If you believe a build has been corrupted
  or want a clean start, you can do `make clean` and then `make`.
* The Cython code assumes C-contiguous arrays; assuming the ordering of an array is
  one way to make the code faster. So if you are going to pass an array to Cython,
  it should be C-contiguous or you will receive an error.
* Cython outputs a shared object (.so) file that is copied into the Python directory.
  Treat it just like a .py file once it is compiled. You cannot edit it directly,
  but you can import it and use its functions from Python like normal.

