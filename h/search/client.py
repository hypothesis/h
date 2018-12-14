# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import elasticsearch


class Client(object):

    """
    A convenience wrapper around a connection to Elasticsearch.

    Holds a connection object, an index name, the elasticsearch library version,
    and the name of the mapping type.

    :param host: Elasticsearch host URL
    :param index: index name
    :param elasticsearch: Elasticsearch library defaulted to elasticsearch
    """

    def __init__(self, host, index, elasticsearch=elasticsearch, **kwargs):
        self._version = elasticsearch.__version__
        self._index = index
        self._conn = elasticsearch.Elasticsearch([host], **kwargs)

        # Our existing Elasticsearch 1.x indexes have a single mapping type
        # "annotation". For ES 6 we should change this to the preferred name
        # of "_doc".
        # See https://www.elastic.co/guide/en/elasticsearch/reference/6.x/removal-of-types.html
        self._mapping_type = "annotation"

    @property
    def index(self):
        return self._index

    @property
    def conn(self):
        return self._conn

    @property
    def mapping_type(self):
        """
        Return the name of the index's mapping type (aka. document type).

        The concept of mapping types is being removed from Elasticsearch and in
        ES >= 6 an index only has a single mapping type.

        See https://www.elastic.co/guide/en/elasticsearch/reference/6.x/removal-of-types.html
        """
        return self._mapping_type

    @property
    def version(self):
        """The version of the elasticsearch library."""
        return self._version


def _get_client_settings(settings):
    kwargs = {}
    kwargs["max_retries"] = settings.get("es.client.max_retries", 3)
    kwargs["retry_on_timeout"] = settings.get("es.client.retry_on_timeout", False)
    kwargs["timeout"] = settings.get("es.client.timeout", 10)

    if "es.client_poolsize" in settings:
        kwargs["maxsize"] = settings["es.client_poolsize"]

    kwargs["verify_certs"] = True
    return kwargs


def get_client(settings):
    """Return a client for the Elasticsearch index."""
    host = settings["es.url"]
    index = settings["es.index"]
    kwargs = _get_client_settings(settings)
    # nb. No AWS credentials here because we assume that if using AWS-managed
    # ES, the cluster lives inside a VPC.
    return Client(host, index, **kwargs)
