#!/bin/bash
# Install the old version of Elasticsearch in /tmp and run it.
set -ev
mkdir /tmp/elasticsearch-old
wget -O - https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-1.6.2.tar.gz | tar xz --directory=/tmp/elasticsearch-old --strip-components=1
/tmp/elasticsearch-old/bin/plugin install elasticsearch/elasticsearch-analysis-icu/2.6.0/
/tmp/elasticsearch-old/bin/elasticsearch -Des.http.poort=9200 -d --path.data /tmp
