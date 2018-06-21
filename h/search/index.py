# -*- coding: utf-8 -*-
"""Functions for updating the search index."""

from __future__ import division, unicode_literals

import logging
import time
from collections import namedtuple

import sqlalchemy as sa
from elasticsearch1 import helpers as es_helpers
from sqlalchemy.orm import subqueryload

from h import models
from h import presenters
from h.events import AnnotationTransformEvent
from h.util.query import column_windows

log = logging.getLogger(__name__)

ES_CHUNK_SIZE = 100
PG_WINDOW_SIZE = 2000


class Window(namedtuple('Window', ['start', 'end'])):
    pass


def index(es, annotation, request, target_index=None):
    """
    Index an annotation into the search index.

    A new annotation document will be created in the search index or,
    if the index already contains an annotation document with the same ID as
    the given annotation then it will be updated.

    :param es: the Elasticsearch client object to use
    :type es: h.search.Client

    :param annotation: the annotation to index
    :type annotation: h.models.Annotation

    :param target_index: the index name, uses default index if not given
    :type target_index: unicode
    """
    presenter = presenters.AnnotationSearchIndexPresenter(annotation)
    annotation_dict = presenter.asdict()

    event = AnnotationTransformEvent(request, annotation, annotation_dict)
    request.registry.notify(event)

    if target_index is None:
        target_index = es.index

    es.conn.index(
        index=target_index,
        doc_type=es.t.annotation,
        body=annotation_dict,
        id=annotation_dict["id"],
    )


def delete(es, annotation_id, target_index=None):
    """
    Mark an annotation as deleted in the search index.

    This will write a new body that only contains the ``deleted`` boolean field
    with the value ``true``. It allows us to rely on Elasticsearch to complain
    about dubious operations while re-indexing when we use `op_type=create`.

    :param es: the Elasticsearch client object to use
    :type es: h.search.Client

    :param annotation_id: the annotation id whose corresponding document to
        delete from the search index
    :type annotation_id: str

    :param target_index: the index name, uses default index if not given
    :type target_index: unicode
    """

    if target_index is None:
        target_index = es.index

    es.conn.index(
        index=target_index,
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

    def index(self, annotation_ids=None, windowsize=PG_WINDOW_SIZE, chunk_size=ES_CHUNK_SIZE):
        """
        Reindex annotations.

        :param annotation_ids: a list of ids to reindex, reindexes all when `None`.
        :type annotation_ids: collection
        :param windowsize: the number of annotations to index in between progress log statements
        :type windowsize: integer
        :param chunk_size: the number of docs in one chunk sent to ES
        :type chunk_size: integer

        :returns: a set of errored ids
        :rtype: set
        """
        if not annotation_ids:
            annotations = _all_annotations(session=self.session, windowsize=windowsize)
        else:
            annotations = _filtered_annotations(session=self.session,
                                                ids=annotation_ids)

        # Report indexing status as we go
        annotations = _log_status(annotations, log_every=windowsize)

        indexing = es_helpers.streaming_bulk(self.es_client.conn, annotations,
                                             chunk_size=chunk_size,
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

        event = AnnotationTransformEvent(self.request, annotation, data)
        self.request.registry.notify(event)

        return (action, data)


def _all_annotations(session, windowsize=2000):
    # This is using a windowed query for loading all annotations in batches.
    # It is the most performant way of loading a big set of records from
    # the database while still supporting eagerloading of associated
    # document data.
    windows = column_windows(session=session,
                             column=models.Annotation.updated,  # implicit ASC
                             windowsize=windowsize,
                             where=_annotation_filter())
    query = _eager_loaded_annotations(session).filter(_annotation_filter())

    for window in windows:
        for a in query.filter(window):
            yield a


def _filtered_annotations(session, ids):
    annotations = (_eager_loaded_annotations(session)
                   .execution_options(stream_results=True)
                   .filter(_annotation_filter())
                   .filter(models.Annotation.id.in_(ids)))

    for a in annotations:
        yield a


def _annotation_filter():
    """Default filter for all search indexing operations."""
    return sa.not_(models.Annotation.deleted)


def _eager_loaded_annotations(session):
    return session.query(models.Annotation).options(
        subqueryload(models.Annotation.document).subqueryload(models.Document.document_uris),
        subqueryload(models.Annotation.document).subqueryload(models.Document.meta),
        subqueryload(models.Annotation.moderation),
        subqueryload(models.Annotation.thread).load_only("id"),
    )


def _log_status(stream, log_every=1000):
    i = 0
    then = time.time()
    for item in stream:
        yield item
        i += 1
        if i % log_every == 0:
            now = time.time()
            delta = now - then
            then = now
            rate = log_every / delta
            log.info('indexed {:d}k annotations, rate={:.0f}/s'
                     .format(i // 1000, rate))
