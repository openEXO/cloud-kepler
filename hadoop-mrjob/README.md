Run cloud-kepler on Gordon
==========================

## Setup Python environment on Gordon

Add:

    module load python scipy

to your `.bashrc`.

all the scripts are setup to use a standard Python environment available in `/home/zonca/py`
in order to launch the python environment in the login node,
run:

    source /home/zonca/py/bin/activate

## Launch a Hadoop job

First it is necessary to start Hadoop on Gordon using:

```
qsub hadoop-cluster.qsub
```

The original script is: <https://github.com/sdsc/sdsc-user/blob/master/jobscripts/gordon/hadoop-cluster.qsub>

Once the job starts, it creates a file `setenv.sourceme` in the folder it was submitted from.

Read the instructions in the file to connect to the Hadoop head node.

## Submit an example word count job to Hadoop

    . run_example_mrjob.sh

Check the output folder `mrjob-wordcount-output/`

## Submit a cloud-kepler job to Hadoop

    . run_mrjob.sh

Check the output folder `mrjob-output/`.

The script takes care of copying the sample input file to HFS, run `bls_pulse.py`,
collect the results and copy the results back to `mrjob-output/`.
The Hadoop job is configured using [mrjob](http://pythonhosted.org/mrjob/).

--
26 Jun 2014 zonca@sdsc.edu
