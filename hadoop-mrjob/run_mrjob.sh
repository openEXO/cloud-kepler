#!/bin/bash

echo "Load the Hadoop environment"
source setenv.sourceme
input_filename="sandbox/eprice/tres2.in"

echo "Making a directory for our input data"
hadoop dfs -mkdir mrjob-input

echo "Copying input text to HDFS"
hadoop dfs -put ../python/$input_filename mrjob-input/$input_filename

echo "Running our mrjob Python script"
./bls_pulse_mrjob.py \
    -r hadoop \
    hdfs:///user/$USER/mrjob-input/$input_filename \
    --jobconf mapred.reduce.tasks=2 \
    --output-dir hdfs:///user/$USER/mrjob-output

echo "Copying the the results back to the local filesystem"
hadoop dfs -get /user/$USER/mrjob-output .

echo "Print some fun job stats"
jobid=$(hadoop job -list all | tail -n1 | awk '{print $1}')
hadoop job -status $jobid
