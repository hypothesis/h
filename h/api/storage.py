# -*- coding: utf-8 -*-
"""
Annotation storage API.

This module provides the core API with access to basic persistence functions
for storing and retrieving annotations. Data passed to these functions is
assumed to be validated.
"""

from functools import partial

from h.api import transform
from h.api import models
from h.api.events import AnnotationBeforeSaveEvent
from h.api.models import elastic
from h.api.models.annotation import Annotation
from h.api.models.document import Document


def annotation_from_dict(data):
    """
    Create an annotation model object from the passed dict, without saving.

    :param data: a dictionary of annotation properties
    :type data: dict

    :returns: the created annotation
    :rtype: dict
    """
    return elastic.Annotation(data)


def fetch_annotation(request, id):
    """
    Fetch the annotation with the given id.

    :param request: the request object
    :type request: pyramid.request.Request

    :param id: the annotation id
    :type id: str

    :returns: the annotation, if found, or None.
    :rtype: dict, NoneType
    """
    if _postgres_enabled(request):
        return request.db.query(Annotation).get(id)

    return elastic.Annotation.fetch(id)


def _legacy_create_annotation_in_elasticsearch(request, data):
    annotation = elastic.Annotation(data)
    # FIXME: this should happen when indexing, not storing.
    _prepare(request, annotation)
    annotation.save()
    return annotation


def _create_annotation(request, data):
    annotation = models.Annotation()

    del data['user']  # The userid from the POSTed data is ignored.
    annotation.userid = request.authenticated_userid

    annotation.text = data.pop('text', None)
    annotation.tags = data.pop('tags', None)

    if data.pop('permissions')['read'] == [annotation.userid]:
        annotation.shared = False
    else:
        annotation.shared = True

    target = data.pop('target', [])
    if target:  # Replies and page notes don't have 'target'.
        target = target[0]  # Multiple targets are ignored.
        annotation.target_selectors = target['selector']

    annotation.target_uri = data.pop('uri')
    annotation.references = data.pop('references', [])

    group = data.pop('group')
    if annotation.is_reply:
        top_level_annotation_id = annotation.references[0]
        top_level_annotation = fetch_annotation(request,
                                                top_level_annotation_id)
        if top_level_annotation:
            annotation.groupid = top_level_annotation.groupid
    else:
        annotation.groupid = group

    annotation.extras = data

    request.db.add(annotation)

    return annotation


def create_annotation(request, data):
    """
    Create an annotation from passed data.

    :param request: the request object
    :type request: pyramid.request.Request

    :param data: a dictionary of annotation properties
    :type data: dict

    :returns: the created annotation
    :rtype: dict
    """
    if request.feature('postgres_write'):
        return _create_annotation(request, data)
    else:
        return _legacy_create_annotation_in_elasticsearch(request, data)


def update_annotation(request, id, data):
    """
    Update the annotation with the given id from passed data.

    This executes a partial update of the annotation identified by `id` using
    the passed data.

    :param request: the request object
    :type request: pyramid.request.Request

    :param id: the annotation id
    :type id: str

    :param data: a dictionary of annotation properties
    :type data: dict

    :returns: the updated annotation
    :rtype: dict
    """
    annotation = elastic.Annotation.fetch(id)
    annotation.update(data)

    # FIXME: this should happen when indexing, not storing.
    _prepare(request, annotation)

    annotation.save()
    return annotation


def delete_annotation(request, id):
    """
    Delete the annotation with the given id.

    :param request: the request object
    :type request: pyramid.request.Request

    :param id: the annotation id
    :type id: str
    """
    annotation = elastic.Annotation.fetch(id)
    annotation.delete()


def expand_uri(request, uri):
    """
    Return all URIs which refer to the same underlying document as `uri`.

    This function determines whether we already have "document" records for the
    passed URI, and if so returns the set of all URIs which we currently
    believe refer to the same document.

    :param request: the request object
    :type request: pyramid.request.Request

    :param uri: a URI associated with the document
    :type id: str

    :returns: a list of equivalent URIs
    :rtype: list
    """
    doc = None
    if _postgres_enabled(request):
        doc = Document.find_by_uris(request.db, [uri]).one_or_none()
    else:
        doc = elastic.Document.get_by_uri(uri)

    if doc is None:
        return [uri]

    # We check if the match was a "canonical" link. If so, all annotations
    # created on that page are guaranteed to have that as their target.source
    # field, so we don't need to expand to other URIs and risk false positives.
    docuris = doc.document_uris
    for docuri in docuris:
        if docuri.uri == uri and docuri.type == 'rel-canonical':
            return [uri]

    return [docuri.uri for docuri in docuris]


def _prepare(request, annotation):
    """Prepare the given annotation for storage."""
    fetcher = partial(fetch_annotation, request)
    transform.prepare(annotation, fetcher)

    # Fire an AnnotationBeforeSaveEvent so subscribers who wish to modify an
    # annotation before save can do so.
    event = AnnotationBeforeSaveEvent(request, annotation)
    request.registry.notify(event)


def _postgres_enabled(request):
    return request.feature('postgres_read')
