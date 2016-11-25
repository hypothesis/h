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
from memex.search.config import (
    configure_index,
    get_aliased_index,
    update_aliased_index,
)

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
    Delete an annotation from the search index.

    If no annotation with the given annotation's ID exists in the search index,
    just log the resulting elasticsearch exception (don't crash).

    :param es: the Elasticsearch client object to use
    :type es: memex.search.Client

    :param annotation_id: the annotation id whose corresponding document to
        delete from the search index
    :type annotation_id: str

    """
    try:
        es.conn.delete(
            index=es.index,
            doc_type=es.t.annotation,
            id=annotation_id,
        )
    except elasticsearch.NotFoundError:
        log.exception('Tried to delete a nonexistent annotation from the '
                      'search index, annotation id: %s', annotation_id)


def reindex(session, es, request):
    """Reindex all annotations into a new index, and update the alias."""

    aliased = get_aliased_index(es) is not None

    # If the index we're using is an alias, then we index into a brand new
    # index and update the alias at the end.
    if aliased:
        new_index = configure_index(es)
        indexer = BatchIndexer(session, es, request, target_index=new_index)
    else:
        indexer = BatchIndexer(session, es, request)

    errored = indexer.index()
    if errored:
        log.debug('failed to index {} annotations, retrying...'.format(
            len(errored)))
        errored = indexer.index(errored)
        if errored:
            log.warn('failed to index {} annotations: {!r}'.format(
                len(errored),
                errored))

    if aliased:
        update_aliased_index(es, new_index)
    else:
        deleter = BatchDeleter(session, es)
        deleter.delete_all()



class BatchIndexer(object):
    """
    A convenience class for reindexing all annotations from the database to
    the search index.
    """

    def __init__(self, session, es_client, request, target_index=None):
        self.session = session
        self.es_client = es_client
        self.request = request

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
                errored.add(item['index']['_id'])
        return errored

    def _prepare(self, annotation):
        action = {'index': {'_index': self._target_index,
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


class BatchDeleter(object):
    """
    A convenience class for removing all annotations that are deleted from the
    database from the search index.
    """

    def __init__(self, session, es_client):
        self.session = session
        self.es_client = es_client

    def delete_all(self):
        """Remove all deleted annotations, and retry failed delete operations once."""
        ids = self.deleted_annotation_ids()
        for _ in range(2):
            if not ids:
                break

            ids = self.delete(ids)
            log.debug(
                'Failed to delete {} annotations, might retry'.format(len(ids)))

    def deleted_annotation_ids(self):
        """
        Get a list of deleted annotation ids by comparing all ids in the search
        index and comparing them to all ids in the database.

        :returns: a set of deleted annotation ids
        :rtype: set
        """
        ids = set()
        for batch in self._batch_iter(2000, self._es_scan()):
            ids.update({a['_id'] for a in batch})

        for batch in self._batch_iter(2000, self._pg_ids()):
            ids.difference_update({a.id for a in batch})
        return ids

    def delete(self, annotation_ids):
        """
        Delete annotations from the search index.

        :param annotation_ids: a list of ids to delete.
        :type annotation_ids: collection

        :returns: a set of errored ids
        :rtype: set
        """
        if not annotation_ids:
            return set()

        deleting = es_helpers.streaming_bulk(self.es_client.conn, annotation_ids,
                                             chunk_size=100,
                                             expand_action_callback=self._prepare,
                                             raise_on_error=False)
        errored = set()
        for ok, item in deleting:
            if not ok and item['delete']['status'] != 404:
                errored.add(item['delete']['_id'])
        return errored

    def _prepare(self, id_):
        action = {'delete': {'_index': self.es_client.index,
                             '_type': self.es_client.t.annotation,
                             '_id': id_}}
        return (action, None)

    def _pg_ids(self):
        # This is using a Postgres cursor for better query performance.
        return self.session.query(models.Annotation.id).execution_options(stream_results=True)

    def _es_scan(self):
        query = {'_source': False, 'query': {'match_all': {}}}
        return es_helpers.scan(self.es_client.conn,
                               index=self.es_client.index,
                               doc_type=self.es_client.t.annotation,
                               query=query)

    def _batch_iter(self, n, iterable):
        it = iter(iterable)
        while True:
            batch = list(itertools.islice(it, n))
            if not batch:
                return
            yield batch
