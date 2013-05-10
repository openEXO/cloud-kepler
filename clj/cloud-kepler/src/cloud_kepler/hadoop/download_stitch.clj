(ns cloud-kepler.hadoop.download-stitch
  (:require
   [cascalog
    conf
    [tap :as tap]
    [workflow :as w]
    [io :as io]
    [api :as api]])
  (:use
   cascalog.api
   [clojure.tools.cli :only (cli)]
   [clojure.string :only (split join)]
   [cascalog.more-taps :only (lfs-delimited)])
  (:import
   [cascading.flow MapReduceFlow]
   [cascading.scheme Scheme TextDelimited TextLine
    TextLine$Compress]
   [cascading.cascade CascadeConnector]
   [org.apache.hadoop.streaming StreamJob]
   [org.apache.hadoop.conf Configuration]
   [org.apache.hadoop.fs
    FileStatus FileSystem LocalFileSystem
    FileUtil Path])
  (:gen-class))

(defn download-stitch-q
  "Creata a download and stitch cascade for the first part of the
   cloud-kepler pipeline."
  [kepler-ids-quarters joined-quarters ;taps
   python jar] ;options
  (let [input (.toString (.getPath (kepler-ids-quarters :source)))
        output (.toString (.getPath (joined-quarters :sink)))
        python-anchor (if jar (last (split jar #"#")) ".")
        map-script (join "/" [python-anchor "python/download.py"])
        mapper (join " " [python map-script])
        reduce-script (join "/" [python-anchor
                                 "python/join_quarters.py"])
        reducer (join " " [python reduce-script])
        job-configuration (StreamJob/createJob
                           (into-array
                            (concat ["-input"  input
                                     "-output" output
                                     "-mapper" mapper
                                     "-reducer" reducer]
                                    (when jar ["-cacheArchive" jar]))))
        flow (MapReduceFlow. "download-stitch" job-configuration)]
    (.connect (CascadeConnector.) (into-array MapReduceFlow [flow]))))

(defn -main
  "Download Kepler FITS files, decode and stitch quarters together."
  [& args]
  (let [[opts remaining help]
        (cli args
             ["--python" "Path to python interpreter"]
             ["--jar" "Path to python jar"]
             )]
    (let [[input-path output-path] remaining
          ;https://groups.google.com/forum/#!msg/cascalog-user/t0LsCp3hxiQ/KpTBSs29lN0J
          input-tap (lfs-delimited input-path)
          output-tap (lfs-delimited output-path)
          download-stitch-cascade (download-stitch-q
                                   input-tap output-tap
                                   (opts :python) (opts :jar))]
       (.complete download-stitch-cascade))))