(ns cloud-kepler.hadoop.bls
  (:use
   [clojure.tools.cli :only (cli)]
   [cloud-kepler.hadoop.utils :as ut])
  (:gen-class))

(defn -main
  "Perform BLS search on a TIME, FLUX and EFLUX time series."
  [& args]
  (let [[opts remaining help]
        (cli args
             ["--python" "Path to python interpreter"]
             ["--jar" "Path to python jar"]
             ["--minper" "minimum period"]
             ["--maxper" "maximum period"]
             ["--mindur" "minimum duration"]
             ["--maxdur" "maximum duration"]
             ["--nsearch" "No of trial periods"]
             ["--nbins" "Number of phase bins"])]
    (let [[input-path output-path] remaining
          ;;https://groups.google.com/forum/#!msg/cascalog-user/t0LsCp3hxiQ/KpTBSs29lN0J
          input-tap (ut/local-tap input-path)
          output-tap (ut/local-tap output-path)
          bls-options-string (clojure.string/join
                              " "
                              [;"--minper" (opts :minper)
                               "--per" (opts :maxper)
                               "--qmin" (opts :mindur)
                               "--qmax" (opts :maxdur)
                               ;"--nsearch" (opts :nsearch)
                               "--nbins" (opts :nbins)
                               ])
          bls-cascade (ut/generalized-python-q
                       input-tap output-tap
                       (opts :python) (opts :jar)
                       "python/bls_pulse.py" bls-options-string
                       nil nil
                       "bls-search")]
       (.complete bls-cascade))))