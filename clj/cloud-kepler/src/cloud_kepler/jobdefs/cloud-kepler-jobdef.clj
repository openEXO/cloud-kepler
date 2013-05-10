;;;;Run cloud-kepler pipeline

(comment
  ***
  Welcome to the cloud-kepler pipeline. Find your Earth-sized planet using the Amazon cloud. 
  ***)

(catch-args
  [:python "python interpreter" nil]
  [:kid-input "Kepler id, quarter input file" nil])

(deflcuster cloud-kepler-cluster
  :num-instances 2
  :spot-task-group "c1.xlarge, 75%, 10"
  :app "cloud-kepler"
  :slave-instance-type "c1.xlarge"
  :master-instance-type "m2.2xlarge"
  :hadoop-config.custom ["-m" "mapred.tasktracker.map.tasks.maximum=8"])

(defstep download-stitch
  :main-class "cloud-kepler.hadoop.download_stitch"
  :step-name "Downoload FITS files and stitch quarters"
  :remote-kic-file "${data-uri}/kic-input.txt"
  :upload ["${kid-input}" :to "${remote-kic-file}"]
  :output-path "${data-uri}/joined-quarters"
  :local {:hadoop-env {"HADOOP_HEAPSIZE" "2048"}
          :python-jar nil
          :num-map-tasks "1"}
  :args.python "${python-interpreter}"
  :args.jar "${python-jar}"
  :args.positional ["${remote-kic-file}" "${output-path}"])

(fire! cloud-kepler-cluster download-stitch)
