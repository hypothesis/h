# -*- coding: utf-8 -*-

"""
HTTP/REST API for storage and retrieval of annotation data.

This module contains the views which implement our REST API, mounted by default
at ``/api``. Currently, the endpoints are limited to:

- basic CRUD (create, read, update, delete) operations on annotations
- annotation search
- a handful of authentication related endpoints

It is worth noting up front that in general, authorization for requests made to
each endpoint is handled outside of the body of the view functions. In
particular, requests to the CRUD API endpoints are protected by the Pyramid
authorization system. You can find the mapping between annotation "permissions"
objects and Pyramid ACLs in :mod:`h.traversal`.
"""
from __future__ import unicode_literals
from pyramid import i18n

from h import search as search_lib
from h import storage
from h.views.api.exceptions import PayloadError
from h.events import AnnotationEvent
from h.interfaces import IGroupService
from h.presenters import AnnotationJSONLDPresenter
from h.traversal import AnnotationContext
from h.schemas.util import validate_query_params
from h.schemas.annotation import (
    CreateAnnotationSchema,
    SearchParamsSchema,
    UpdateAnnotationSchema,
)
from h.views.api.config import api_config

_ = i18n.TranslationStringFactory(__package__)


@api_config(
    versions=["v1", "v2"],
    route_name="api.search",
    link_name="search",
    description="Search for annotations",
)
def search(request):
    """Search the database for annotations matching with the given query."""
    schema = SearchParamsSchema()
    params = validate_query_params(schema, request.params)

    separate_replies = params.pop("_separate_replies", False)

    stats = getattr(request, "stats", None)

    search = search_lib.Search(request, separate_replies=separate_replies, stats=stats)
    result = search.run(params)

    svc = request.find_service(name="annotation_json_presentation")

    out = {"total": result.total, "rows": svc.present_all(result.annotation_ids)}

    if separate_replies:
        out["replies"] = svc.present_all(result.reply_ids)

    return out


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotations",
    request_method="POST",
    permission="create",
    link_name="annotation.create",
    description="Create an annotation",
)
def create(request):
    """Create an annotation from the POST payload."""
    schema = CreateAnnotationSchema(request)
    appstruct = schema.validate(_json_payload(request))
    group_service = request.find_service(IGroupService)
    annotation = storage.create_annotation(request, appstruct, group_service)

    _publish_annotation_event(request, annotation, "create")

    svc = request.find_service(name="annotation_json_presentation")
    annotation_resource = _annotation_resource(request, annotation)
    return svc.present(annotation_resource)


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation",
    request_method="GET",
    permission="read",
    link_name="annotation.read",
    description="Fetch an annotation",
)
def read(context, request):
    """Return the annotation (simply how it was stored in the database)."""
    svc = request.find_service(name="annotation_json_presentation")
    return svc.present(context)


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation.jsonld",
    request_method="GET",
    permission="read",
)
def read_jsonld(context, request):
    request.response.content_type = "application/ld+json"
    request.response.content_type_params = {
        "charset": "UTF-8",
        "profile": str(AnnotationJSONLDPresenter.CONTEXT_URL),
    }
    presenter = AnnotationJSONLDPresenter(context)
    return presenter.asdict()


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation",
    request_method=("PATCH", "PUT"),
    permission="update",
    link_name="annotation.update",
    description="Update an annotation",
)
def update(context, request):
    """Update the specified annotation with data from the PATCH payload."""
    if request.method == "PUT" and hasattr(request, "stats"):
        request.stats.incr("api.deprecated.put_update_annotation")

    schema = UpdateAnnotationSchema(
        request, context.annotation.target_uri, context.annotation.groupid
    )
    appstruct = schema.validate(_json_payload(request))
    group_service = request.find_service(IGroupService)

    annotation = storage.update_annotation(
        request, context.annotation.id, appstruct, group_service
    )

    _publish_annotation_event(request, annotation, "update")

    svc = request.find_service(name="annotation_json_presentation")
    annotation_resource = _annotation_resource(request, annotation)
    return svc.present(annotation_resource)


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation",
    request_method="DELETE",
    permission="delete",
    link_name="annotation.delete",
    description="Delete an annotation",
)
def delete(context, request):
    """Delete the specified annotation."""
    annotation_delete_service = request.find_service(name="annotation_delete")
    annotation_delete_service.delete(context.annotation)

    # TODO: Track down why we don't return an HTTP 204 like other DELETEs
    return {"id": context.annotation.id, "deleted": True}


def _json_payload(request):
    """
    Return a parsed JSON payload for the request.

    :raises PayloadError: if the body has no valid JSON body
    """
    try:
        return request.json_body
    except ValueError:
        raise PayloadError()


def _publish_annotation_event(request, annotation, action):
    """Publish an event to the annotations queue for this annotation action."""
    event = AnnotationEvent(request, annotation.id, action)
    request.notify_after_commit(event)


def _annotation_resource(request, annotation):
    group_service = request.find_service(IGroupService)
    links_service = request.find_service(name="links")
    return AnnotationContext(annotation, group_service, links_service)
