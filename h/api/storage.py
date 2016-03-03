# -*- coding: utf-8 -*-
"""
Annotation storage API.

This module provides the core API with access to basic persistence functions
for storing and retrieving annotations. Data passed to these functions is
assumed to be validated.
"""

from functools import partial

from h.api import transform
from h.api.events import AnnotationBeforeSaveEvent
from h.api.models import elastic
from h.api.models.annotation import Annotation


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

    :param id: the annotation id
    :type id: str

    :returns: the annotation, if found, or None.
    :rtype: dict, NoneType
    """
    if _postgres_enabled(request):
        return request.db.query(Annotation).get(id)

    return elastic.Annotation.fetch(id)


def create_annotation(request, data):
    """
    Create an annotation from passed data.

    :param data: a dictionary of annotation properties
    :type data: dict

    :returns: the created annotation
    :rtype: dict
    """
    annotation = elastic.Annotation(data)

    # FIXME: this should happen when indexing, not storing.
    _prepare(request, annotation)

    annotation.save()
    return annotation


def update_annotation(request, id, data):
    """
    Update the annotation with the given id from passed data.

    This executes a partial update of the annotation identified by `id` using
    the passed data.

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

    :param id: the annotation id
    :type id: str
    """
    annotation = elastic.Annotation.fetch(id)
    annotation.delete()


def expand_uri(uri):
    """
    Return all URIs which refer to the same underlying document as `uri`.

    This function determines whether we already have "document" records for the
    passed URI, and if so returns the set of all URIs which we currently
    believe refer to the same document.

    :param uri: a URI associated with the document
    :type id: str

    :returns: a list of equivalent URIs
    :rtype: list
    """
    doc = elastic.Document.get_by_uri(uri)
    if doc is None:
        return [uri]

    # We check if the match was a "canonical" link. If so, all annotations
    # created on that page are guaranteed to have that as their target.source
    # field, so we don't need to expand to other URIs and risk false positives.
    for link in doc.get('link', []):
        if link.get('href') == uri and link.get('rel') == 'canonical':
            return [uri]

    return doc.uris()


def _prepare(request, annotation):
    """
    Prepare the given annotation for storage.

    Scan the passed annotation for any target URIs or document metadata URIs
    and add normalized versions of these to the document.
    """
    fetcher = partial(fetch_annotation, request)
    transform.set_group_if_reply(annotation, fetcher=fetcher)
    transform.insert_group_if_none(annotation)
    transform.set_group_permissions(annotation)

    # FIXME: Remove this in a month or so, when all our clients have been
    # updated. -N 2015-09-25
    transform.fix_old_style_comments(annotation)

    # FIXME: When this becomes simply part of a search indexing operation, this
    # should probably not mutate its argument.
    transform.normalize_annotation_target_uris(annotation)

    # Fire an AnnotationBeforeSaveEvent so subscribers who wish to modify an
    # annotation before save can do so.
    event = AnnotationBeforeSaveEvent(request, annotation)
    request.registry.notify(event)


def _postgres_enabled(request):
    return request.feature('postgres_read')
