# -*- coding: utf-8 -*-

import elasticsearch


class Client(object):

    """
    A convenience wrapper around a connection to Elasticsearch.

    Holds a connection object, an index name, and an enumeration of document
    types stored in the index.

    :param host: Elasticsearch host URL
    :param index: index name
    """

    class t(object):
        """Document types"""
        annotation = 'annotation'
        document = 'document'

    def __init__(self, host, index, **kwargs):
        self.index = index
        self.conn = elasticsearch.Elasticsearch([host],
                                                verify_certs=True,
                                                **kwargs)
