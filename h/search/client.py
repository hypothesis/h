# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import certifi
from elasticsearch1 import Elasticsearch, RequestsHttpConnection
from elasticsearch import Elasticsearch as Elasticsearch6
from requests_aws4auth import AWS4Auth

# TODO - Can we remove this?
__all__ = ('Client',)


class Client(object):

    """
    A convenience wrapper around a connection to Elasticsearch 1.x.

    Holds a connection object, an index name, and an enumeration of document
    types stored in the index.

    :param host: Elasticsearch host URL
    :param index: index name
    """

    class t(object):  # noqa
        """Document types"""
        annotation = 'annotation'

    def __init__(self, host, index, **kwargs):
        self._index = index
        self._conn = Elasticsearch([host],
                                   verify_certs=True,
                                   # N.B. this won't be necessary if we upgrade
                                   # to elasticsearch>=5.0.0.
                                   ca_certs=certifi.where(),
                                   **kwargs)

    @property
    def index(self):
        return self._index

    @property
    def conn(self):
        return self._conn

    @property
    def using_es6(self):
        return False


class Elasticsearch6Client(object):
    """
    A convenience wrapper around a connection to Elasticsearch 6.x.

    Holds a connection object, an index name, and an enumeration of document
    types stored in the index.

    :param host: Elasticsearch host URL
    :param index: index name
    """

    # Document ("mapping") types are deprecated in Elasticsearch.
    # ES 6 only allows one mapping type per index. Fortunately that is all we
    # need. If we want to index other types of object in future, we will either
    # need to use separate indexes or a custom `type` flag per document.
    #
    # See https://www.elastic.co/guide/en/elasticsearch/reference/6.x/removal-of-types.html
    class t(object):  # noqa
        """Document types"""

        # The mapping type name `_doc` is the preferred value in ES 6 for
        # forward compatibility with ES 7.
        annotation = '_doc'

    def __init__(self, host, index, **kwargs):
        self._index = index
        self._conn = Elasticsearch6([host], **kwargs)

    @property
    def index(self):
        return self._index

    @property
    def conn(self):
        return self._conn

    @property
    def using_es6(self):
        return True


def get_client(settings):
    """Return a client for the Elasticsearch index."""
    host = settings['es.host']
    index = settings['es.index']
    kwargs = {}
    kwargs['max_retries'] = settings.get('es.client.max_retries', 3)
    kwargs['retry_on_timeout'] = settings.get('es.client.retry_on_timeout', False)
    kwargs['timeout'] = settings.get('es.client.timeout', 10)

    if 'es.client_poolsize' in settings:
        kwargs['maxsize'] = settings['es.client_poolsize']

    have_aws_creds = ('es.aws.access_key_id' in settings and
                      'es.aws.region' in settings and
                      'es.aws.secret_access_key' in settings)

    if have_aws_creds:
        auth = AWS4Auth(settings['es.aws.access_key_id'],
                        settings['es.aws.secret_access_key'],
                        settings['es.aws.region'],
                        'es')
        kwargs['http_auth'] = auth
        kwargs['connection_class'] = RequestsHttpConnection

    return Client(host, index, **kwargs)


def get_es6_client(settings):
    """Return a client for the Elasticsearch 6 index."""
    host = settings['es.url']
    index = settings['es.index']
    kwargs = {}
    kwargs['max_retries'] = settings.get('es.client.max_retries', 3)
    kwargs['retry_on_timeout'] = settings.get('es.client.retry_on_timeout', False)
    kwargs['timeout'] = settings.get('es.client.timeout', 10)

    if 'es.client_poolsize' in settings:
        kwargs['maxsize'] = settings['es.client_poolsize']

    # nb. No AWS credentials here because we assume that if using AWS-managed
    # ES, the cluster lives inside a VPC.
    return Elasticsearch6Client(host, index, **kwargs)
