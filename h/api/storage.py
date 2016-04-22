# -*- coding: utf-8 -*-
"""
Annotation storage API.

This module provides the core API with access to basic persistence functions
for storing and retrieving annotations. Data passed to these functions is
assumed to be validated.
"""

from functools import partial

from pyramid import i18n

from h.api import transform
from h.api import models
from h.api.events import AnnotationBeforeSaveEvent
from h.api.db import types


_ = i18n.TranslationStringFactory(__package__)


def annotation_from_dict(data):
    """
    Create an annotation model object from the passed dict, without saving.

    :param data: a dictionary of annotation properties
    :type data: dict

    :returns: the created annotation
    :rtype: dict
    """
    return models.elastic.Annotation(data)


def fetch_annotation(request, id, _postgres=None):
    """
    Fetch the annotation with the given id.

    :param request: the request object
    :type request: pyramid.request.Request

    :param id: the annotation id
    :type id: str

    :returns: the annotation, if found, or None.
    :rtype: dict, NoneType
    """
    # If no postgres arg is passed then decide whether to use postgres based
    # on the postgres feature flag.
    if _postgres is None:
        _postgres = _postgres_enabled(request)

    if _postgres:
        try:
            return request.db.query(models.Annotation).get(id)
        except types.InvalidUUID:
            return None

    return models.elastic.Annotation.fetch(id)


def legacy_create_annotation(request, data):
    annotation = models.elastic.Annotation(data)
    # FIXME: this should happen when indexing, not storing.
    _prepare(request, annotation)
    annotation.save()
    return annotation


def update_document_metadata(db,
                             annotation,
                             document_meta_dicts,
                             document_uri_dicts):
    documents = models.Document.find_or_create_by_uris(
        db,
        annotation.target_uri,
        [u['uri'] for u in document_uri_dicts],
        created=annotation.created,
        updated=annotation.updated)

    if documents.count() > 1:
        document = models.merge_documents(db,
                                          documents,
                                          updated=annotation.updated)
    else:
        document = documents.first()

    document.updated = annotation.updated

    for document_uri_dict in document_uri_dicts:
        models.create_or_update_document_uri(
            session=db,
            document=document,
            created=annotation.created,
            updated=annotation.updated,
            **document_uri_dict)

    for document_meta_dict in document_meta_dicts:
        models.create_or_update_document_meta(
            session=db,
            document=document,
            created=annotation.created,
            updated=annotation.updated,
            **document_meta_dict)


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
    document_uri_dicts = data['document']['document_uri_dicts']
    document_meta_dicts = data['document']['document_meta_dicts']
    del data['document']

    annotation = models.Annotation(**data)
    request.db.add(annotation)

    # We need to flush the db here so that annotation.created and
    # annotation.updated get created.
    request.db.flush()

    update_document_metadata(
        request.db, annotation, document_meta_dicts, document_uri_dicts)

    return annotation


def update_annotation(session, annotation_id, data):
    """
    Update an existing annotation and its associated document metadata.

    Update the annotation identified by annotation_id with the given
    data. Create, delete and update document metadata as appropriate.

    :param session: the database session
    :type session: sqlalchemy.orm.session.Session

    :param annotation_id: the ID of the annotation to be updated, this is
        assumed to be a validated ID of an annotation that does already exist
        in the database
    :type annotation_id: string

    :param data: the validated data with which to update the annotation
    :type data: dict

    :returns: the created annotation
    :rtype: h.api.models.Annotation

    """
    document_uri_dicts = data['document']['document_uri_dicts']
    document_meta_dicts = data['document']['document_meta_dicts']
    del data['document']

    annotation = models.Annotation.query.get(annotation_id)

    for key, value in data.items():
        setattr(annotation, key, value)

    update_document_metadata(
        session, annotation, document_meta_dicts, document_uri_dicts)

    return annotation


def legacy_update_annotation(request, id, data):
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
    annotation = models.elastic.Annotation.fetch(id)
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
    if _postgres_enabled(request):
        annotation = fetch_annotation(request, id, _postgres=True)
        request.db.delete(annotation)

    legacy_annotation = fetch_annotation(request, id, _postgres=False)
    legacy_annotation.delete()


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
        doc = models.Document.find_by_uris(request.db, [uri]).one_or_none()
    else:
        doc = models.elastic.Document.get_by_uri(uri)

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
    fetcher = partial(fetch_annotation, request, _postgres=False)
    transform.prepare(annotation, fetcher)

    # Fire an AnnotationBeforeSaveEvent so subscribers who wish to modify an
    # annotation before save can do so.
    event = AnnotationBeforeSaveEvent(request, annotation)
    request.registry.notify(event)


def _postgres_enabled(request):
    return request.feature('postgres')
