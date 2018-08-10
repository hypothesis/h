#!/bin/bash
# Install Elasticsearch in /tmp and run it.
set -ev
mkdir /tmp/elasticsearch
wget -O - https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.2.4.tar.gz | tar xz --directory=/tmp/elasticsearch --strip-components=1
/tmp/elasticsearch/bin/elasticsearch-plugin install analysis-icu
/tmp/elasticsearch/bin/elasticsearch -E http.port=9200 -E path.data=/tmp/elasticsearch_data -d
