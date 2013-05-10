(defproject cloud-kepler "1.0.0-SNAPSHOT"
  ;https://github.com/maoe/rrd4clj/issues/1
  :description "Cloud Kepler Cascading wrappers"
  :repositories [["spymemcached" "http://files.couchbase.com/maven2"]]

  ;:dev-dependencies [[swank-clojure "1.4.0-SNAPSHOT"]]
  
  :dependencies [[org.clojure/clojure "1.3.0"]

                 [cascalog "1.8.6"]
                 [org.clojure/tools.cli "0.2.1"]
                                        ;[org.apache.maven/super-pom "2.0"]
                 [clj-http "0.3.6"]
                 [cascading/cascading-core "1.2.4"
                  :exclusions [org.codehaus.janino/janino
                               thirdparty/jgrapht-jdk1.6
                               riffle/riffle]]
                 [org.apache.hadoop/hadoop-streaming "0.20.2"]
                 [cascalog "1.8.6"]
                 ]

  ;Define AOT classes
  :aot [cloud-kepler.hadoop.download-stitch])