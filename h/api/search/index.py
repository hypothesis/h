# -*- coding: utf-8 -*-
"""Functions for updating the search index."""

from __future__ import unicode_literals
import itertools
import logging

import elasticsearch
from elasticsearch import helpers as es_helpers

from h.api import models
from h.api import presenters
from h.api.events import AnnotationTransformEvent


log = logging.getLogger(__name__)


def index(es, annotation, request):
    """
    Index an annotation into the search index.

    A new annotation document will be created in the search index or,
    if the index already contains an annotation document with the same ID as
    the given annotation then it will be updated.

    :param es: the Elasticsearch client object to use
    :type es: h.api.search.Client

    :param annotation: the annotation to index
    :type annotation: h.api.models.Annotation

    """
    annotation_dict = presenters.AnnotationJSONPresenter(
        request, annotation).asdict()

    annotation_dict['target'][0]['scope'] = [
        annotation.target_uri_normalized]

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
    :type es: h.api.search.Client

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
