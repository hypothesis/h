# -*- coding: utf-8 -*-

import elasticsearch

from h.api import presenters


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

    def index_annotation(self, request, annotation):
        """
        Index an annotation into the search index.

        A new annotation document will be created in the search index or,
        if the index already contains an annotation document with the id
        annotation_dict['id'] it will be updated.

        """
        annotation_dict = presenters.AnnotationJSONPresenter(
            request, annotation).asdict()

        annotation_dict['target'][0]['scope'] = [
            annotation.target_uri_normalized]

        self.conn.index(
            index=self.index,
            doc_type=self.t.annotation,
            body=annotation_dict,
            id=annotation_dict["id"],
        )
