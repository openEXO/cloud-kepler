This directory contains a script that generates job submission files for an HTCondor
cluster. In particular, it outputs a script `condor_submit_all.sh` that, when run,
submits all the generated jobs, and a single script for each individual job. To
generate your input files, run

    python geninput.py <path_to_infile> <path_to_configfile>
    
Two directories, `condor_input` and `condor_output`, are also created; all the 
output (STDOUT, STDERR, and logging) from HTCondor will appear in the 
`condor_output` directory with consistent filenames.

Because the cluster crashed the last time we tried to submit 200,000 jobs at one time,
`geninput.py` offers an option `-n <N>` for specifying the number of stars `N` per job 
that should be created. In this case, instead of naming files `KIC*.*`, the files will 
have randomly-generated filenames that will still be consistent between STDERR, STOUT,
and logging. This is a good practice when submitting large jobs but there is a
performance decrease associated with it; use with caution.

Valid examples of calling the `geninput` script:

    python geninput.py ../python/sandbox/eprice/koilist.in pulse.conf
    python geninput.py -n 1000 ../python/sandbox/eprice/targets.in pulse.conf

Useful HTCondor commands
------------------------

- To remove all your jobs that are not currently running: `condor_rm -constraint 'JobStatus =!= 2'`
- To remove (kill) a job that is running: `condor_rm <JobID> -name <MachineName>`; for example, `condor_rm 5580.0 -name science3.stsci.edu`
- To see the number of jobs in your queue: `condor_q -submitter <user>`; for example, `condor_q -submitter eprice`
