echo "Load the Hadoop environment"
source setenv.sourceme

echo "Making a directory for our input data"
hadoop dfs -mkdir mrjob-input

echo "Copying input text to HDFS"
hadoop dfs -put ../test/test_011446443.txt mrjob-input/test_011446443.txt

echo "Running our mrjob Python script"
./bls_pulse_mrjob.py \
    -r hadoop \
    hdfs:///user/$USER/mrjob-input/test_011446443.txt \
    --jobconf mapred.reduce.tasks=2 \
    --output-dir hdfs:///user/$USER/mrjob-output

echo "Copying the the results back to the local filesystem"
hadoop dfs -get /user/$USER/mrjob-output .

echo "Print some fun job stats"
jobid=$(hadoop job -list all | tail -n1 | awk '{print $1}')
hadoop job -status $jobid
