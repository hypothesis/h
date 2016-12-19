# -*- coding: utf-8 -*-
"""Functions for updating the search index."""

from __future__ import unicode_literals

import itertools
import logging
from collections import namedtuple

import elasticsearch
from elasticsearch import helpers as es_helpers
from sqlalchemy.orm import subqueryload

from memex import models
from memex import presenters
from memex._compat import xrange
from memex.events import AnnotationTransformEvent

log = logging.getLogger(__name__)


class Window(namedtuple('Window', ['start', 'end'])):
    pass


def index(es, annotation, request):
    """
    Index an annotation into the search index.

    A new annotation document will be created in the search index or,
    if the index already contains an annotation document with the same ID as
    the given annotation then it will be updated.

    :param es: the Elasticsearch client object to use
    :type es: memex.search.Client

    :param annotation: the annotation to index
    :type annotation: memex.models.Annotation

    """
    presenter = presenters.AnnotationSearchIndexPresenter(annotation)
    annotation_dict = presenter.asdict()

    event = AnnotationTransformEvent(request, annotation_dict)
    request.registry.notify(event)

    es.conn.index(
        index=es.index,
        doc_type=es.t.annotation,
        body=annotation_dict,
        id=annotation_dict["id"],
    )


def delete(es, annotation_id):
    """
    Mark an annotation as deleted in the search index.

    This will write a new body that only contains the ``deleted`` boolean field
    with the value ``true``. It allows us to rely on Elasticsearch to complain
    about dubious operations while re-indexing when we use `op_type=create`.

    :param es: the Elasticsearch client object to use
    :type es: memex.search.Client

    :param annotation_id: the annotation id whose corresponding document to
        delete from the search index
    :type annotation_id: str

    """
    es.conn.index(
        index=es.index,
        doc_type=es.t.annotation,
        body={'deleted': True},
        id=annotation_id)


class BatchIndexer(object):
    """
    A convenience class for reindexing all annotations from the database to
    the search index.
    """

    def __init__(self, session, es_client, request, target_index=None, op_type='index'):
        self.session = session
        self.es_client = es_client
        self.request = request
        self.op_type = op_type

        # By default, index into the open index
        if target_index is None:
            self._target_index = self.es_client.index
        else:
            self._target_index = target_index

    def index(self, annotation_ids=None):
        """
        Reindex annotations.

        :param annotation_ids: a list of ids to reindex, reindexes all when `None`.
        :type annotation_ids: collection

        :returns: a set of errored ids
        :rtype: set
        """
        if not annotation_ids:
            annotations = self._stream_all_annotations()
        else:
            annotations = self._stream_filtered_annotations(annotation_ids)

        indexing = es_helpers.streaming_bulk(self.es_client.conn, annotations,
                                             chunk_size=100,
                                             raise_on_error=False,
                                             expand_action_callback=self._prepare)
        errored = set()
        for ok, item in indexing:
            if not ok:
                status = item[self.op_type]

                was_doc_exists_err = 'document already exists' in status['error']
                if self.op_type == 'create' and was_doc_exists_err:
                    continue

                errored.add(status['_id'])
        return errored

    def _prepare(self, annotation):
        action = {self.op_type: {'_index': self._target_index,
                                 '_type': self.es_client.t.annotation,
                                 '_id': annotation.id}}
        data = presenters.AnnotationSearchIndexPresenter(annotation).asdict()

        event = AnnotationTransformEvent(self.request, data)
        self.request.registry.notify(event)

        return (action, data)

    def _stream_all_annotations(self, chunksize=2000):
        # This is using a windowed query for loading all annotations in batches.
        # It is the most performant way of loading a big set of records from
        # the database while still supporting eagerloading of associated
        # document data.

        updated = self.session.query(models.Annotation.updated). \
                execution_options(stream_results=True). \
                order_by(models.Annotation.updated.desc()).all()

        count = len(updated)
        windows = [Window(start=updated[min(x+chunksize, count)-1].updated,
                          end=updated[x].updated)
                   for x in xrange(0, count, chunksize)]
        basequery = self._eager_loaded_query().order_by(models.Annotation.updated.asc())

        for window in windows:
            in_window = models.Annotation.updated.between(window.start, window.end)
            for a in basequery.filter(in_window):
                yield a

    def _stream_filtered_annotations(self, annotation_ids):
        annotations = self._eager_loaded_query(). \
            execution_options(stream_results=True). \
            filter(models.Annotation.id.in_(annotation_ids))

        for a in annotations:
            yield a

    def _eager_loaded_query(self):
        return self.session.query(models.Annotation).options(
            subqueryload(models.Annotation.document).subqueryload(models.Document.document_uris),
            subqueryload(models.Annotation.document).subqueryload(models.Document.meta)
        )
