# -*- coding: utf-8 -*-
"""
Annotation storage API.

This module provides the core API with access to basic persistence functions
for storing and retrieving annotations. Data passed to these functions is
assumed to be validated.
"""

from h.api import models
from h.api import search


def fetch_annotation(id):
    """
    Fetch the annotation with the given id.

    :param id: the annotation id
    :type id: str

    :returns: the annotation, if found, or None.
    :rtype: dict, NoneType
    """
    return models.Annotation.fetch(id)


def create_annotation(data):
    """
    Create an annotation from passed data.

    :param data: a dictionary of annotation properties
    :type data: dict

    :returns: the created annotation
    :rtype: dict
    """
    annotation = models.Annotation(data)

    # FIXME: this should happen when indexing, not storing.
    search.prepare(annotation)

    annotation.save()
    return annotation


def update_annotation(id, data):
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
    annotation = models.Annotation.fetch(id)
    annotation.update(data)

    # FIXME: this should happen when indexing, not storing.
    search.prepare(annotation)

    annotation.save()
    return annotation


def delete_annotation(id):
    """
    Delete the annotation with the given id.

    :param id: the annotation id
    :type id: str
    """
    annotation = models.Annotation.fetch(id)
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
    doc = models.Document.get_by_uri(uri)
    if doc is None:
        return [uri]

    # We check if the match was a "canonical" link. If so, all annotations
    # created on that page are guaranteed to have that as their target.source
    # field, so we don't need to expand to other URIs and risk false positives.
    for link in doc.get('link', []):
        if link.get('href') == uri and link.get('rel') == 'canonical':
            return [uri]

    return doc.uris()
