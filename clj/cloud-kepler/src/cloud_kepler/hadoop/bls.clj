(defn bls-q
  "Run BLS"
  (:import)
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
          input-tap (lfs-delimited input-path)
          output-tap (lfs-delimited output-path)
          download-stitch-cascade (ut/generalized-python-q
                                   input-tap output-tap
                                   (opts :python) (opts :jar)
                                   "python/bls_search.py" nil
                                   nil nil
                                   "bls-search")]
       (.complete bls-cascade))))