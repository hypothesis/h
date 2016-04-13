# -*- coding: utf-8 -*-
"""Functions for updating the search index."""

from __future__ import unicode_literals

import elasticsearch

from h.api import presenters


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

    es.conn.index(
        index=es.index,
        doc_type=es.t.annotation,
        body=annotation_dict,
        id=annotation_dict["id"],
    )
