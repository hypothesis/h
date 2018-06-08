# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from elasticsearch_dsl import connections


def connect(hosts, alias="default", **kwargs):
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
    connections.create_connection(alias, hosts=hosts, verify_certs=True, **kwargs)
