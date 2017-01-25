# -*- coding: utf-8 -*-

import certifi
from elasticsearch import Elasticsearch

__all__ = ('Client',)


class Client(object):

    """
    A convenience wrapper around a connection to Elasticsearch.

    Holds a connection object, an index name, and an enumeration of document
    types stored in the index.

    :param host: Elasticsearch host URL
    :param index: index name
    """

    class t(object):  # noqa
        """Document types"""
        annotation = 'annotation'

    def __init__(self, host, index, **kwargs):
        self.index = index
        self.conn = Elasticsearch([host],
                                  verify_certs=True,
                                  # N.B. this won't be necessary if we upgrade
                                  # to elasticsearch>=5.0.0.
                                  ca_certs=certifi.where(),
                                  **kwargs)


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

    return Client(host, index, **kwargs)
