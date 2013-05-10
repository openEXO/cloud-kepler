(ns cloud-kepler.download-stitch
  (:use
   cascalog.api
   [clijure.tools.cli :only (cli)]
   [clojure.string :only (split join)])
  (:import
   [cascading.flow MapReduceFlow]
   [cascading.cascade CascadeConnector])
  (:gen-class))

(defn -main
  "Download Kepler FITS files, decode and stitch quarters together.")