echo "Load the Hadoop environment"
source setenv.sourceme
input_filename=README.md

echo "Making a directory for our input data"
hadoop dfs -mkdir mrjob-input

echo "Copying input text to HDFS"
hadoop dfs -put $input_filename mrjob-input/$input_filename

echo "Running our mrjob Python script"
python mr_word_freq_count.py \
    -r hadoop \
    hdfs:///user/$USER/mrjob-input/$input_filename \
    --jobconf mapred.reduce.tasks=2 \
    --output-dir hdfs:///user/$USER/mrjob-wordcount-output

echo "Copying the the results back to the local filesystem"
hadoop dfs -get /user/$USER/mrjob-wordcount-output .

echo "Print some fun job stats"
jobid=$(hadoop job -list all | tail -n1 | awk '{print $1}')
hadoop job -status $jobid
