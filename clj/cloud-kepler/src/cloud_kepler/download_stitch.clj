(ns cloud-kepler.download-stitch
  (:use
   cascalog.api
   [clojure.tools.cli :only (cli)]
   [clojure.string :only (split join)])
  (:import
   [cascading.flow MapReduceFlow]
   [cascading.cascade CascadeConnector]
   [org.apache.hadoop.fs
    FileStatus FileSystem LocalFileSystem
    FileUtil Path])
  (:gen-class))

(defn -main
  "Download Kepler FITS files, decode and stitch quarters together."
  [& args]
  (let [[opts remaining help]
        (cli args
             ["--python" "Path to python interpreter"]
             )]
    (let [[input-path output-path] remaining
          input-tap (format-tab-tap input-tap)
          output-tap (format-tab-tap output-tap)
          download-stitch-cascade (download-stitch-q
                                   input-tap output-tap
                                   (opts :python))
          (.complete download-stitch-cascade)])))