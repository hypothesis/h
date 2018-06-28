# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import certifi
import elasticsearch1
import elasticsearch
from requests_aws4auth import AWS4Auth


class Client(object):

    """
    A convenience wrapper around a connection to Elasticsearch.

    Holds a connection object, an index name, and the name of the mapping type.

    :param host: Elasticsearch host URL
    :param index: index name
    :param elasticsearch: Elasticsearch library defaulted to elasticsearch1
    """

    def __init__(self, host, index, elasticsearch=elasticsearch1, **kwargs):
        self._index = index
        self._conn = elasticsearch.Elasticsearch([host],
                                                 **kwargs)

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


def _get_client_settings(settings):
    kwargs = {}
    kwargs['max_retries'] = settings.get('es.client.max_retries', 3)
    kwargs['retry_on_timeout'] = settings.get('es.client.retry_on_timeout', False)
    kwargs['timeout'] = settings.get('es.client.timeout', 10)

    if 'es.client_poolsize' in settings:
        kwargs['maxsize'] = settings['es.client_poolsize']

    kwargs['verify_certs'] = True
    return kwargs


def get_client(settings):
    """Return a client for the Elasticsearch index."""
    host = settings['es.host']
    index = settings['es.index']
    kwargs = _get_client_settings(settings)
    # N.B. this won't be necessary if we upgrade
    # to elasticsearch>=5.0.0.
    kwargs['ca_certs'] = certifi.where()
    have_aws_creds = ('es.aws.access_key_id' in settings and
                      'es.aws.region' in settings and
                      'es.aws.secret_access_key' in settings)
    if have_aws_creds:
        auth = AWS4Auth(settings['es.aws.access_key_id'],
                        settings['es.aws.secret_access_key'],
                        settings['es.aws.region'],
                        'es')
        kwargs['http_auth'] = auth
        kwargs['connection_class'] = elasticsearch1.RequestsHttpConnection
    return Client(host, index, **kwargs)


def get_es6_client(settings):
    """Return a client for the Elasticsearch 6 index."""
    host = settings['es.url']
    index = settings['es.index']
    kwargs = _get_client_settings(settings)
    # nb. No AWS credentials here because we assume that if using AWS-managed
    # ES, the cluster lives inside a VPC.
    return Client(host, index, elasticsearch=elasticsearch, **kwargs)
