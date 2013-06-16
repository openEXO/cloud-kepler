;;;;Run cloud-kepler pipeline

(comment
  ***
  Welcome to the cloud-kepler pipeline. Find your Earth-sized planet using the Amazon cloud.
  ***)

(catch-args
  [:python "python interpreter" nil]
  ;http://stackoverflow.com/questions/1252965/distributing-my-python-scripts-as-jars-with-jython
  [:python-jar "Path to the python jar" nil]
  [:kid-input "Kepler id, quarter input file" nil]
  [:min-per "Minimum planetary ortbital period" 1.5]
  [:max-per "Maximum planetrary orbital period" 100.]
  [:min-dur "Minimum duration of transit in hours" 1.5]
  [:max-dur "Maximum duration of transit in hours" 15.]
  [:nsearch "Number of trial periods" 100]
  [:nbins "Number of phase bins" 100])

(add-validators
  (val-opts :required [:python :kid-input :python-jar
                       :min-per :max-per :min-dur :max-dur
                       :nsearch :nbins]))

(defcluster cloud-kepler-cluster
  :num-instances 2
  :spot-task-group "c1.xlarge,75%,10"
  :jar-src-path "clj/cloud-kepler/target/cloud-kepler-1.0.0-SNAPSHOT-standalone.jar"

  :local {:hadoop-env {"HADOOP_HEAPSIZE" "2048"}
          :python-jar "."
          :num-map-tasks "1"
          :python "python"
          :kid-input "test/test_q1.txt"}

  :app "cloud-kepler"
  :keypair "only_local"
  :slave-instance-type "c1.xlarge"
  :master-instance-type "m2.2xlarge"
  :hadoop-config.custom ["-m" "mapred.tasktracker.map.tasks.maximum=8"])

(defstep download-stitch
  :main-class "cloud_kepler.hadoop.download_stitch"
  :step-name "Downoload FITS files and stitch quarters"
  :remote-kic-file "${data-uri}/kic-input.txt"
  :upload ["${kid-input}" :to "${remote-kic-file}"]
  :stitched-path "${data-uri}/joined-quarters"
  :args.python "${python}"
  :args.jar "${python-jar}"
  :args.positional ["${remote-kic-file}" "${stitched-path}"])

(defstep bls-search
  :main-class "cloud_kepler.hadoop.bls"
  :step-name "Perform Box Least Square period finding"
  :bls-output-path "${data-uri}/bls-output"
  :stitched-path "${data-uri}/joined-quarters"
  :args.python "${python}"
  :args.jar "${python-jar}"
  :args.minper "${min-per}"
  :args.maxper "${max-per}"
  :args.mindur "${min-dur}"
  :args.maxdur "${max-dur}"
  :args.nsearch "${nsearch}"
  :args.nbins "${nbins}"
  :args.positional ["${stitched-path}" "${bls-output-path}"])

(fire! cloud-kepler-cluster download-stitch bls-search)
