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
   [cascalog.more-taps :only (lfs-delimited)]
   [cloud-kepler.hadoop.utils :as ut])
  (:gen-class))

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
          download-stitch-cascade (ut/generalized-python-q
                                   input-tap output-tap
                                   (opts :python) (opts :jar)
                                   "python/download.py" nil
                                   "python/join-quarters.py" nil
                                   "download-join")]
       (.complete download-stitch-cascade))))