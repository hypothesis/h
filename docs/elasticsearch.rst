ElasticSearch
#############

The h project uses ElasticSearch_ (v1.0 or later) as its principal data store
for annotation data, and requires the `ElasticSearch ICU Analysis`_ plugin to be
installed.

Installing
----------

1.  Install ElasticSearch. It is best to follow the instructions provided by the
    ElasticSearch project for `installing the package on your platform`_.
2.  Install the ICU Analysis plugin using the `instructions provided`_. **NB:**
    ensure you install the correct version of the plugin for your version of
    ElasticSearch.

.. _ElasticSearch: https://www.elastic.co/products/elasticsearch
.. _ElasticSearch ICU Analysis: https://github.com/elastic/elasticsearch-analysis-icu
.. _installing the package on your platform: https://www.elastic.co/downloads/elasticsearch
.. _instructions provided: https://github.com/elastic/elasticsearch-analysis-icu#icu-analysis-for-elasticsearch

Troubleshooting
---------------

By default, ElasticSearch may try to join other nodes on the network resulting
in ``IndexAlreadyExists`` errors at startup. See the documentation for how to
turn off discovery.
