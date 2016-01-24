# -*- coding: utf-8 -*-

import elasticsearch


class Client(object):

    """
    A convenience wrapper around a connection to ElasticSearch.

    Holds a connection object, an index name, and an enumeration of document
    types stored in the index.

    :param host: ElasticSearch host URL
    :param index: index name
    """

    class t(object):
        """Document types"""
        annotation = 'annotation'
        document = 'document'

    def __init__(self, host, index):
        self.index = index
        self.conn = elasticsearch.Elasticsearch([host], verify_certs=True)
