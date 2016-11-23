# -*- coding: utf-8 -*-

import certifi
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

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

    def get_aliased_index(self):
        """
        Fetch the name of the underlying index.

        Returns ``None`` if the index is not aliased or does not exist.
        """
        try:
            result = self.conn.indices.get_alias(name=self.index)
        except NotFoundError:  # no alias with that name
            return None
        if len(result) > 1:
            raise RuntimeError("We don't support managing aliases that "
                               "point to multiple indices at the moment!")
        return result.keys()[0]

    def update_aliased_index(self, new_target):
        """
        Update the alias to point to a new target index.

        Will raise `RuntimeError` if the index is not aliased or does not
        exist.
        """
        old_target = self.get_aliased_index()
        if old_target is None:
            raise RuntimeError("Cannot update aliased index for index that "
                               "is not already aliased.")

        self.conn.indices.update_aliases(body={
            'actions': [
                {'add': {'index': new_target, 'alias': self.index}},
                {'remove': {'index': old_target, 'alias': self.index}},
            ],
        })
