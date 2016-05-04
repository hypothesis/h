# -*- coding: utf-8 -*-
"""Functions for updating the search index."""

from __future__ import unicode_literals
import logging

import elasticsearch

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

    :param annotation: the annotation whose corresponding document to delete
        from the search index
    :type annotation: h.api.models.Annotation

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
