Quickstart Guide
****************

A normal run of cloud-kepler can be started by::

    more input.txt | python get_data.py mast | python join_quarters.py | python drive_bls_pulse.py -c config.conf

This sequence downloads all data from MAST and runs it through the algorithm with the
parameters in a configuration file.


Specifying the data to download
===============================

The input file (or lines typed directly to ``stdin``) should include the KIC ID, quarter 
number, and cadence identifier on each line, such as::

    011013072   1   llc
    011013072   2   slc
    011600006   *   llc

The special quarter identifier ``*`` will download all available quarters for the given
KIC ID. ``slc`` indicates short-cadence data and ``llc`` indicates long-cadence data.

The Python script ``get_data.py`` also accepts the keyword ``data`` followed by an absolute
or relative filepath of a top-level data directory, with the same structure as the 
*Kepler* archive on MAST; use this option instead of ``mast`` if your data is stored 
locally.


Configuration file options
==========================

There are several options that can be specified in a configuration file; the same options
can be specified via command line options, but they will be overriden by the file if it
is provided (with the ``-c`` flag). A standard configuration file looks like::

    [DEFAULT]
    segment = 2
    min_duration = 0.01
    max_duration = 0.5
    n_bins = 1000
    direction = 0
    mode = cython
    print_format = encode
    verbose = no
    profiling = off

Additional options will be added as needed, such as for detrending flags.

