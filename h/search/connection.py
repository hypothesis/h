# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from elasticsearch_dsl import connections

# TODO: Temporary hard-coding of ELASTICSEARCH_URL: this should come from settings
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9201")


# TODO: Make `hosts` a required argument
def connect(hosts=[ELASTICSEARCH_URL], **kwargs):
    """
    Establish a 'default` connection to Elasticsearch

    This establishes a connection to newer (v6.x) Elasticsearch which is
    available as the 'default' connection henceforth via `elasticsearch_dsl`

    e.g. `elasticsearch_dsl.get_connection()`
    """
    connections.create_connection(hosts=hosts, **kwargs)
