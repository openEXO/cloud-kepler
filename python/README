This branch is a stripped down Cython implementation of the master branch code. A few 
things to keep in mind if you are working on this branch:

* Cython code must be compiled for changes to take effect. To compile, just run
  `make` from the Python base directory. If you believe a build has been corrupted
  or want a clean start, you can do `make clean` and then `make`.
* My Cython code assumes C-contiguous arrays; assuming the ordering of an array is
  one way to make the code faster. So if you are going to pass an array to Cython,
  it should be C-contiguous or you will receive an error.
* Cython outputs a shared object (.so) file that I copy into the Python directory.
  Treat it just like a .py file once it is compiled. You cannot edit it directly,
  but you can import it and use its functions from Python like normal.

