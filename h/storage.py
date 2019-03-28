# -*- coding: utf-8 -*-
"""
Annotation storage API.

This module provides the core API with access to basic persistence functions
for storing and retrieving annotations. Data passed to these functions is
assumed to be validated.
"""
from __future__ import unicode_literals

# FIXME: This module was originally written to be a single point of
#        indirection through which the storage backend could be swapped out on
#        the fly. This helped us to migrate from Elasticsearch-based
#        persistence to PostgreSQL persistence.
#
#        The purpose of this module is now primarily to serve as a place to
#        wrap up the business logic of creating and retrieving annotations. As
#        such, it probably makes more sense for this to be split up into a
#        couple of different services at some point.

from datetime import datetime

from pyramid import i18n

from h import models, schemas
from h.db import types
from h.util.group_scope import url_in_scope
from h.models.document import update_document_metadata

_ = i18n.TranslationStringFactory(__package__)


def fetch_annotation(session, id_):
    """
    Fetch the annotation with the given id.

    :param session: the database session
    :type session: sqlalchemy.orm.session.Session

    :param id_: the annotation ID
    :type id_: str

    :returns: the annotation, if found, or None.
    :rtype: h.models.Annotation, NoneType
    """
    try:
        return session.query(models.Annotation).get(id_)
    except types.InvalidUUID:
        return None


def fetch_ordered_annotations(session, ids, query_processor=None):
    """
    Fetch all annotations with the given ids and order them based on the list
    of ids.

    The optional `query_processor` parameter allows for passing in a function
    that can change the query before it is run, especially useful for
    eager-loading certain data. The function will get the query as an argument
    and has to return a query object again.

    :param session: the database session
    :type session: sqlalchemy.orm.session.Session

    :param ids: the list of annotation ids
    :type ids: list

    :param query_processor: an optional function that takes the query and
                            returns an updated query
    :type query_processor: callable

    :returns: the annotation, if found, or None.
    :rtype: h.models.Annotation, NoneType
    """
    if not ids:
        return []

    ordering = {x: i for i, x in enumerate(ids)}

    query = session.query(models.Annotation).filter(models.Annotation.id.in_(ids))
    if query_processor:
        query = query_processor(query)

    anns = sorted(query, key=lambda a: ordering.get(a.id))
    return anns


def create_annotation(request, data, group_service):
    """
    Create an annotation from already-validated data.

    :param request: the request object
    :type request: pyramid.request.Request

    :param data: an annotation data dict that has already been validated by
        :py:class:`h.schemas.annotation.CreateAnnotationSchema`
    :type data: dict

    :param group_service: a service object that implements
        :py:class:`h.interfaces.IGroupService`
    :type group_service: :py:class:`h.interfaces.IGroupService`

    :returns: the created and flushed annotation
    :rtype: :py:class:`h.models.Annotation`
    """
    created = updated = datetime.utcnow()

    document_uri_dicts = data["document"]["document_uri_dicts"]
    document_meta_dicts = data["document"]["document_meta_dicts"]
    del data["document"]

    # Replies must have the same group as their parent.
    if data["references"]:
        top_level_annotation_id = data["references"][0]
        top_level_annotation = fetch_annotation(request.db, top_level_annotation_id)
        if top_level_annotation:
            data["groupid"] = top_level_annotation.groupid
        else:
            raise schemas.ValidationError(
                "references.0: "
                + _("Annotation {id} does not exist").format(id=top_level_annotation_id)
            )

    # The user must have permission to create an annotation in the group
    # they've asked to create one in. If the application didn't configure
    # a groupfinder we will allow writing this annotation without any
    # further checks.
    group = group_service.find(data["groupid"])
    if group is None or not request.has_permission("write", context=group):
        raise schemas.ValidationError(
            "group: " + _("You may not create annotations " "in the specified group!")
        )

    _validate_group_scope(group, data["target_uri"])

    annotation = models.Annotation(**data)
    annotation.created = created
    annotation.updated = updated

    document = update_document_metadata(
        request.db,
        annotation.target_uri,
        document_meta_dicts,
        document_uri_dicts,
        created=created,
        updated=updated,
    )
    annotation.document = document

    request.db.add(annotation)
    request.db.flush()

    return annotation


def update_annotation(request, id_, data, group_service):
    """
    Update an existing annotation and its associated document metadata.

    Update the annotation identified by ``id_`` with the given
    data. Create, delete and update document metadata as appropriate.

    :param request: the request object

    :param id_: the ID of the annotation to be updated, this is assumed to be a
        validated ID of an annotation that does already exist in the database
    :type id_: string

    :param data: the validated data with which to update the annotation
    :type data: dict

    :type group_service: :py:class:`h.interfaces.IGroupService`

    :returns: the updated annotation
    :rtype: h.models.Annotation

    """
    updated = datetime.utcnow()

    # Remove any 'document' field first so that we don't try to save it on the
    # annotation object.
    document = data.pop("document", None)

    annotation = request.db.query(models.Annotation).get(id_)
    annotation.updated = updated

    group = group_service.find(annotation.groupid)
    if group is None:
        raise schemas.ValidationError(
            "group: " + _("Invalid group specified for annotation")
        )
    if data.get("target_uri", None):
        _validate_group_scope(group, data["target_uri"])

    annotation.extra.update(data.pop("extra", {}))

    for key, value in data.items():
        setattr(annotation, key, value)

    if document:
        document_uri_dicts = document["document_uri_dicts"]
        document_meta_dicts = document["document_meta_dicts"]
        document = update_document_metadata(
            request.db,
            annotation.target_uri,
            document_meta_dicts,
            document_uri_dicts,
            updated=updated,
        )
        annotation.document = document

    return annotation


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
        if docuri.uri == uri and docuri.type == "rel-canonical":
            return [uri]

    return [docuri.uri for docuri in docuris]


def _validate_group_scope(group, target_uri):
    # If no scopes are present, or if the group is configured to allow
    # annotations outside of its scope, there's nothing to do here
    if not group.scopes or group.enforce_scope is False:
        return
    # The target URI must match at least one
    # of a group's defined scopes, if the group has any
    group_scopes = [scope.scope for scope in group.scopes]
    if not url_in_scope(target_uri, group_scopes):
        raise schemas.ValidationError(
            "group scope: "
            + _("Annotations for this target URI " "are not allowed in this group")
        )
