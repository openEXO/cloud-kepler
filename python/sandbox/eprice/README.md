Running with a configuration file
---------------------------------

To run `cloud-kepler` with a configuration file specifying parameters, the following command will work (for example):

    more sandbox/eprice/input.txt | python get_data.py disk sandbox/eprice/data | python join_quarters.py | python drive_bls_pulse_config.py sandbox/eprice/pulse.conf

There is an example configuration file in this directory, and the input file here will work with the included data files.
