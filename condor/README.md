This directory contains a script that generates job submission files for an HTCondor
cluster. In particular, it outputs a script `condor_submit_all.sh` that, when run,
submits all the generated jobs, and a single script for each individual job. To
generate your input files, run

    python geninput.py <path_to_infile> <path_to_configfile>
    
Two directories, `condor_input` and `condor_output`, are also created; all the 
output (STDOUT, STDERR, and logging) from HTCondor will appear in the 
`condor_output` directory with consistent filenames.

Useful HTCondor commands
------------------------

- To remove all your jobs that are not currently running: `condor_rm -constraint 'JobStatus =!= 2'`
- Continue this list...
