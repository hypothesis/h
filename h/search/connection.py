# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from elasticsearch_dsl import connections

# TODO: Temporary hard-coding of ELASTICSEARCH_URL: this should come from settings
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9201")


# TODO: Make `hosts` a required argument
def connect(alias='default', hosts=[ELASTICSEARCH_URL], **kwargs):
    """
    Establish a connection to Elasticsearch through elasticsearch_dsl

    This establishes a connection to newer (v6.x) Elasticsearch. Unless the
    `alias` parameter has a value other than "default", this connection will
    then be available as the 'default' connection for `elasticsearch_dsl`

    e.g. `elasticsearch_dsl.connections.get_connection()` will return the
    connection established here

    kwargs get passed on to Elasticsearch

    .. seealso:: https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch

    :param alias: The alias to use for referencing the created connection. Will
                  create a "default" connection unless this param has a value
                  other than `default`
    :param hosts: List of host(s) (e.g. 'http://foo.com:9200') to connect to
    """
    connections.create_connection(alias,
                                  hosts=hosts,
                                  verify_certs=True,
                                  **kwargs)
