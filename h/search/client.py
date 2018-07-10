# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import certifi
from elasticsearch1 import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

__all__ = ('Client',)


class Client(object):

    """
    A convenience wrapper around a connection to Elasticsearch.

    Holds a connection object, an index name, and the name of the mapping type.

    :param host: Elasticsearch host URL
    :param index: index name
    """

    def __init__(self, host, index, **kwargs):
        self._index = index
        self._conn = Elasticsearch([host],
                                   verify_certs=True,
                                   # N.B. this won't be necessary if we upgrade
                                   # to elasticsearch>=5.0.0.
                                   ca_certs=certifi.where(),
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
