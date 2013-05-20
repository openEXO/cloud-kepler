(ns cloud-kepler.hadoop.utils
  (:import
   [cascading.flow MapReduceFlow]
   [org.apache.hadoop.streaming StreamJob]
   [cascading.cascade CascadeConnector])
  (:use
   [clojure.string :only (split join)]
   [cascalog.more-taps :only (lfs-delimited)])
  (:gen-class))

(defn local-tap
  [path]
  (lfs-delimited path))

(defn generalized-python-q
  "Create a generalized mapper and reducer q that calls python streaming
 scripts"
  [input-tap output-tap
   python jar
   python-mapper python-mapper-options
   python-reducer python-reducer-options
   name-flow]
  (let [input (.toString (.getPath (input-tap :source)))
        output (.toString (.getPath (output-tap :sink)))
        python-anchor (if jar (last (split jar #"#")) ".")
        map-script (join "/" [python-anchor python-mapper])
        mapper (join " " [python map-script python-mapper-options])
        reduce-script (join "/" [python-anchor python-reducer])
        reducer (join " " [python reduce-script python-reducer-options])
        stream-args (if (nil? python-reducer)
                      ["-input"  input
                       "-output" output
                       "-mapper" mapper]
                      ["-input"  input
                       "-output" output
                       "-mapper" mapper
                       "-reducer" reducer])
        job-configuration (StreamJob/createJob
                           (into-array
                            (concat
                             stream-args
                             ;;(when jar ["-cacheArchive" jar])
                             )))
        flow (MapReduceFlow. name-flow job-configuration)]
    (.connect (CascadeConnector.) (into-array MapReduceFlow [flow]))))