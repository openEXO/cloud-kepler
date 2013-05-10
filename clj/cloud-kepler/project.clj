(defproject cloud-kepler "1.0.0-SNAPSHOT"
  :description "Cloud Kepler Cascading wrappers"
  :dependencies [[org.clojure/clojure "1.3.0"]
                 [cascalog "1.8.5"]
                 [org.clojure/tools.cli "0.2.1"]
                 [cascading/cascading-core "1.2.4"]
                 [org.apache.hadoop/hadoop-streaming "0.20.2"]]

  ;Define AOT classes
  :aot [cloud-kepler.download-stitch])