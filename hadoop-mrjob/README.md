Run cloud-kepler on Gordon
==========================

- You must be in the bash shell from the beginning.

- It is STRONGLY advised that you immediately start a screen session on the login node, so that if you start a long job on the compute node you don't need to leave that terminal up for the entire duration.  This can be accomplished by:

    screen -S <choose_a_screen_session_name>

To detach a screen session:

    Ctrl-A, Ctrl-D

To reattach a screen session:

    screen -ls
    screen -r <the_full_name_of_your_session_including_numbers>

## Setup Python environment on Gordon

Add:

    module load python scipy

to your `.bashrc`.

all the scripts are setup to use a standard Python environment available in `/home/zonca/py`
in order to launch the python environment in the login node,
run:

    source /home/zonca/py/bin/activate
    
If successful, you should see a (py) in front of your unix prompt.

## Launch a Hadoop job

First it is necessary to start Hadoop on Gordon using:

```
    qsub hadoop-cluster.qsub

```
which is inside the folder "hadoop-mrjob" at the main level.

The original script is: <https://github.com/sdsc/sdsc-user/blob/master/jobscripts/gordon/hadoop-cluster.qsub>

You will need to monitor the output of:

```
    qstat -u <your_user_name>
```

One good way to do this is via the following command:

    watch -n 2 qstat -u <your_user_name>

Once the job starts (the "S" column goes from 'Q' to 'R'), it creates a file `setenv.sourceme` in the folder it was submitted from.

Read the instructions in `setenv.sourceme` to connect to the Hadoop head node (basically, it will tell you which compute node to ssh into, e.g., `ssh gcn-??-??`).  Once ssh'd into the compute node, you should activate the python virtual environment again (depending on your default shell, you may or may not need to do the first part):

    bash
    module load python scipy
    source /home/zonca/py/bin/activate
    cd <path in `setenv.sourceme`>
    source setenv.source

You will want to verify the bls_pulse parameters are correct, paying particular attention to things like the "fits_dir" parameter (make sure you have write access to this location before submitting your job!).
    
    more pulse.conf

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
