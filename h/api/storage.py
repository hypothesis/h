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
