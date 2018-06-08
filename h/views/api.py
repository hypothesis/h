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
from pyramid import security

from h import search as search_lib
from h import storage
from h.exceptions import PayloadError
from h.events import AnnotationEvent
from h.interfaces import IGroupService
from h.presenters import AnnotationJSONLDPresenter
from h.traversal import AnnotationContext
from h.schemas.annotation import CreateAnnotationSchema, UpdateAnnotationSchema
from h.views.api_config import api_config, AngularRouteTemplater

_ = i18n.TranslationStringFactory(__package__)


@api_config(route_name="api.index")
def index(context, request):
    """Return the API descriptor document.

    Clients may use this to discover endpoints for the API.
    """

    api_links = request.registry.api_links

    # We currently need to keep a list of the parameter names we use in our API
    # paths and pass these explicitly into the templater. As and when new
    # parameter names are added, we'll need to add them here, or this view will
    # break (and get caught by the `test_api_index` functional test).
    templater = AngularRouteTemplater(request.route_url, params=["id", "pubid", "user"])

    links = {}
    for link in api_links:
        method_info = {
            "method": link["method"],
            "url": templater.route_template(link["route_name"]),
            "desc": link["description"],
        }
        _set_at_path(links, link["name"].split("."), method_info)

    return {"links": links}


@api_config(
    route_name="api.links",
    link_name="links",
    renderer="json_sorted",
    description="URL templates for generating URLs for HTML pages",
)
def links(context, request):
    templater = AngularRouteTemplater(request.route_url, params=["user"])

    tag_search_url = request.route_url("activity.search", _query={"q": "_query_"})
    tag_search_url = tag_search_url.replace("_query_", 'tag:":tag"')

    oauth_authorize_url = request.route_url("oauth_authorize")
    oauth_revoke_url = request.route_url("oauth_revoke")

    return {
        "account.settings": request.route_url("account"),
        "forgot-password": request.route_url("forgot_password"),
        "groups.new": request.route_url("group_create"),
        "help": request.route_url("help"),
        "oauth.authorize": oauth_authorize_url,
        "oauth.revoke": oauth_revoke_url,
        "search.tag": tag_search_url,
        "signup": request.route_url("signup"),
        "user": templater.route_template("stream.user_query"),
    }


@api_config(
    route_name="api.search", link_name="search", description="Search for annotations"
)
def search(request):
    """Search the database for annotations matching with the given query."""
    params = request.params.copy()

    separate_replies = params.pop("_separate_replies", False)
    stats = getattr(request, "stats", None)
    result = search_lib.Search(
        request, separate_replies=separate_replies, stats=stats
    ).run(params)

    svc = request.find_service(name="annotation_json_presentation")

    out = {"total": result.total, "rows": svc.present_all(result.annotation_ids)}

    if separate_replies:
        out["replies"] = svc.present_all(result.reply_ids)

    return out


@api_config(
    route_name="api.annotations",
    request_method="POST",
    effective_principals=security.Authenticated,
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


@api_config(route_name="api.annotation.jsonld", request_method="GET", permission="read")
def read_jsonld(context, request):
    request.response.content_type = "application/ld+json"
    request.response.content_type_params = {
        "charset": "UTF-8",
        "profile": str(AnnotationJSONLDPresenter.CONTEXT_URL),
    }
    presenter = AnnotationJSONLDPresenter(context)
    return presenter.asdict()


@api_config(
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
    route_name="api.annotation",
    request_method="DELETE",
    permission="delete",
    link_name="annotation.delete",
    description="Delete an annotation",
)
def delete(context, request):
    """Delete the specified annotation."""
    storage.delete_annotation(request.db, context.annotation.id)

    # N.B. We publish the original model (including all the original annotation
    # fields) so that queue subscribers have context needed to decide how to
    # process the delete event. For example, the streamer needs to know the
    # target URLs of the deleted annotation in order to know which clients to
    # forward the delete event to.
    _publish_annotation_event(request, context.annotation, "delete")

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


def _set_at_path(dict_, path, value):
    """
    Set the value at a given `path` within a nested `dict`.

    :param dict_: The root `dict` to update
    :param path: List of path components
    :param value: Value to assign
    """
    key = path[0]
    if key not in dict_:
        dict_[key] = {}

    if len(path) == 1:
        dict_[key] = value
    else:
        _set_at_path(dict_[key], path[1:], value)


def _annotation_resource(request, annotation):
    group_service = request.find_service(IGroupService)
    links_service = request.find_service(name="links")
    return AnnotationContext(annotation, group_service, links_service)
