(defproject cloud-kepler "1.0.0-SNAPSHOT"
  :description "Cloud Kepler Cascading wrappers"
  :repositories [["spymemcached" "http://files.couchbase.com/maven2"]]

  :dev-dependencies [[swank-clojure "1.4.0-SNAPSHOT"]]
  
  :dependencies [[org.clojure/clojure "1.3.0"]
                 [cascalog "1.8.5"]
                 [org.clojure/tools.cli "0.2.1"]
                 [org.apache.maven/super-pom "2.0"]
                 [cascading/cascading-core "2.0.8"]
                 ;[org.apache.hadoop/hadoop-streaming "0.20.2"]
                 ;[cascalog "1.8.6"]
                 ]

  ;Define AOT classes
  :aot [cloud-kepler.hadoop.download-stitch])