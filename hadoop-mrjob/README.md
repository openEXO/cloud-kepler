Run cloud-kepler on Gordon
==========================

First it is necessary to start Hadoop on Gordon using:

https://github.com/sdsc/sdsc-user/blob/master/jobscripts/gordon/hadoop-cluster.qsub

Once the job starts, it creates a file `setenv.sourceme` in
the folder it was submitted from.

The file contains the address of the Hadoop head node, `ssh` into that node and run:

    . run_mrjob.sh

The script takes care of copying the sample input file to HFS, run `bls_pulse.py`,
collect the results and copy the results back to `mrjob-output/`.
The Hadoop job is configured using [mrjob](http://pythonhosted.org/mrjob/).

--
16 Dec 2013 zonca@sdsc.edu
