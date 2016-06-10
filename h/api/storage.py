# -*- coding: utf-8 -*-
"""
Annotation storage API.

This module provides the core API with access to basic persistence functions
for storing and retrieving annotations. Data passed to these functions is
assumed to be validated.
"""

from pyramid import i18n

from h.api import schemas
from h.api import models
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


def fetch_annotation(session, id_):
    """
    Fetch the annotation with the given id.

    :param session: the database session
    :type session: sqlalchemy.orm.session.Session

    :param id_: the annotation ID
    :type id_: str

    :returns: the annotation, if found, or None.
    :rtype: h.api.models.Annotation, NoneType
    """
    try:
        return session.query(models.Annotation).get(id_)
    except types.InvalidUUID:
        return None


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

    # Replies must have the same group as their parent.
    if data['references']:
        top_level_annotation_id = data['references'][0]
        top_level_annotation = fetch_annotation(request.db,
                                                top_level_annotation_id)
        if top_level_annotation:
            data['groupid'] = top_level_annotation.groupid
        else:
            raise schemas.ValidationError(
                'references.0: ' +
                _('Annotation {id} does not exist').format(
                    id=top_level_annotation_id)
            )

    # The user must have permission to create an annotation in the group
    # they've asked to create one in.
    if data['groupid'] != '__world__':
        group_principal = 'group:{}'.format(data['groupid'])
        if group_principal not in request.effective_principals:
            raise schemas.ValidationError('group: ' +
                                          _('You may not create annotations '
                                            'in groups you are not a member '
                                            'of!'))

    annotation = models.Annotation(**data)
    request.db.add(annotation)

    # We need to flush the db here so that annotation.created and
    # annotation.updated get created.
    request.db.flush()

    models.update_document_metadata(
        request.db, annotation, document_meta_dicts, document_uri_dicts)

    return annotation


def update_annotation(session, id_, data):
    """
    Update an existing annotation and its associated document metadata.

    Update the annotation identified by id_ with the given
    data. Create, delete and update document metadata as appropriate.

    :param session: the database session
    :type session: sqlalchemy.orm.session.Session

    :param id_: the ID of the annotation to be updated, this is assumed to be a
        validated ID of an annotation that does already exist in the database
    :type id_: string

    :param data: the validated data with which to update the annotation
    :type data: dict

    :returns: the updated annotation
    :rtype: h.api.models.Annotation

    """
    # Remove any 'document' field first so that we don't try to save it on the
    # annotation object.
    document = data.pop('document', None)

    annotation = session.query(models.Annotation).get(id_)

    annotation.extra.update(data.pop('extra', {}))

    for key, value in data.items():
        setattr(annotation, key, value)

    if document:
        document_uri_dicts = document['document_uri_dicts']
        document_meta_dicts = document['document_meta_dicts']
        models.update_document_metadata(
            session, annotation, document_meta_dicts, document_uri_dicts)

    return annotation


def delete_annotation(session, id_):
    """
    Delete the annotation with the given id.

    :param session: the database session
    :type session: sqlalchemy.orm.session.Session

    :param id_: the annotation ID
    :type id_: str
    """
    session.query(models.Annotation).filter_by(id=id_).delete()


def expand_uri(session, uri):
    """
    Return all URIs which refer to the same underlying document as `uri`.

    This function determines whether we already have "document" records for the
    passed URI, and if so returns the set of all URIs which we currently
    believe refer to the same document.

    :param session: the database session
    :type session: sqlalchemy.orm.session.Session

    :param uri: a URI associated with the document
    :type uri: str

    :returns: a list of equivalent URIs
    :rtype: list
    """
    doc = models.Document.find_by_uris(session, [uri]).one_or_none()

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
