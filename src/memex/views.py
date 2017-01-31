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
objects and Pyramid ACLs in :mod:`memex.resources`.
"""
from pyramid import i18n
from pyramid import security
from pyramid.view import view_config
from sqlalchemy.orm import subqueryload
import venusian

from memex import cors
from memex import models
from memex.events import AnnotationEvent
from memex.interfaces import IGroupService
from memex.presenters import AnnotationJSONPresenter
from memex.presenters import AnnotationJSONLDPresenter
from memex.resources import AnnotationResource
from memex import search as search_lib
from memex import schemas
from memex import storage

_ = i18n.TranslationStringFactory(__package__)

cors_policy = cors.policy(
    allow_headers=(
        'Authorization',
        'Content-Type',
        'X-Annotator-Auth-Token',
        'X-Client-Id',
    ),
    allow_methods=('HEAD', 'GET', 'POST', 'PUT', 'DELETE'),
    allow_preflight=True)


class APIError(Exception):

    """Base exception for problems handling API requests."""

    def __init__(self, message, status_code=500):
        self.status_code = status_code
        super(APIError, self).__init__(message)


class PayloadError(APIError):

    """Exception raised for API requests made with missing/invalid payloads."""

    def __init__(self):
        super(PayloadError, self).__init__(
            _('Expected a valid JSON payload, but none was found!'),
            status_code=400
        )


def api_config(link_name=None, description=None, **settings):
    """
    A view configuration decorator with defaults.

    JSON in and out. CORS with tokens and client id but no cookie.

    :param link_name: The dotted path to the metadata for this view in the
                      `api.index` route output.
    :param description: Description of the view included in the `api.index`
                        route output.
    """

    # Save the initial request method here before we add others (eg. OPTIONS)
    # later for CORS support.
    initial_request_method = settings.get('request_method', 'GET')

    # Callback which adds the view's metadata to the list of API links returned
    # by the /api index root
    def register_api_link(context, name, ob):
        link = {'name': link_name,
                'method': initial_request_method,
                'route_name': settings.get('route_name'),
                'description': description,
                }

        registry = context.config.registry
        if not hasattr(registry, 'api_links'):
            registry.api_links = []
        registry.api_links.append(link)

    settings.setdefault('accept', 'application/json')
    settings.setdefault('renderer', 'json')
    settings.setdefault('decorator', cors_policy)

    request_method = settings.get('request_method', ())
    if not isinstance(request_method, tuple):
        request_method = (request_method,)
    if len(request_method) == 0:
        request_method = ('DELETE', 'GET', 'HEAD', 'POST', 'PUT',)
    settings['request_method'] = request_method + ('OPTIONS',)

    def config(wrapped):
        if link_name:
            venusian.attach(wrapped, register_api_link, category='pyramid')
        return view_config(**settings)(wrapped)

    return config


@api_config(context=APIError)
def error_api(context, request):
    request.response.status_code = context.status_code
    return {'status': 'failure', 'reason': context.message}


@api_config(context=schemas.ValidationError)
def error_validation(context, request):
    request.response.status_code = 400
    return {'status': 'failure', 'reason': context.message}


@api_config(route_name='api.index')
def index(context, request):
    """Return the API descriptor document.

    Clients may use this to discover endpoints for the API.
    """

    api_links = request.registry.api_links

    links = {}
    for link in api_links:
        method_info = {
            'method': link['method'],

            # For routes that include an id, generate a route URL with `:id` in
            # the output. We can't just use `:id` as the `id` param value because
            # `route_url` URL-encodes parameters.
            'url': request.route_url(link['route_name'],
                                     id='_id_').replace('_id_', ':id'),
            'desc': link['description'],
        }
        _set_at_path(links, link['name'].split('.'), method_info)

    return {
        'message': "Annotator Store API",
        'links': links,
    }


@api_config(route_name='api.search',
            link_name='search',
            description='Search for annotations')
def search(request):
    """Search the database for annotations matching with the given query."""
    params = request.params.copy()

    separate_replies = params.pop('_separate_replies', False)
    stats = getattr(request, 'stats', None)
    result = search_lib.Search(request,
                               separate_replies=separate_replies,
                               stats=stats).run(params)

    out = {
        'total': result.total,
        'rows': _present_annotations(request, result.annotation_ids)
    }

    if separate_replies:
        out['replies'] = _present_annotations(request, result.reply_ids)

    return out


@api_config(route_name='api.annotations',
            request_method='POST',
            effective_principals=security.Authenticated,
            link_name='annotation.create',
            description='Create an annotation')
def create(request):
    """Create an annotation from the POST payload."""
    schema = schemas.CreateAnnotationSchema(request)
    appstruct = schema.validate(_json_payload(request))
    group_service = request.find_service(IGroupService)
    annotation = storage.create_annotation(request, appstruct, group_service)

    _publish_annotation_event(request, annotation, 'create')

    links_service = request.find_service(name='links')
    group_service = request.find_service(IGroupService)
    resource = AnnotationResource(annotation, group_service, links_service)
    presenter = AnnotationJSONPresenter(resource)
    return presenter.asdict()


@api_config(route_name='api.annotation',
            request_method='GET',
            permission='read',
            link_name='annotation.read',
            description='Fetch an annotation')
def read(context, request):
    """Return the annotation (simply how it was stored in the database)."""
    presenter = AnnotationJSONPresenter(context)
    return presenter.asdict()


@api_config(route_name='api.annotation.jsonld',
            request_method='GET',
            permission='read')
def read_jsonld(context, request):
    request.response.content_type = 'application/ld+json'
    request.response.content_type_params = {
        'profile': AnnotationJSONLDPresenter.CONTEXT_URL}
    presenter = AnnotationJSONLDPresenter(context)
    return presenter.asdict()


@api_config(route_name='api.annotation',
            request_method='PUT',
            permission='update',
            link_name='annotation.update',
            description='Update an annotation')
def update(context, request):
    """Update the specified annotation with data from the PUT payload."""
    schema = schemas.UpdateAnnotationSchema(request,
                                            context.annotation.target_uri,
                                            context.annotation.groupid)
    appstruct = schema.validate(_json_payload(request))

    annotation = storage.update_annotation(request.db,
                                           context.annotation.id,
                                           appstruct)

    _publish_annotation_event(request, annotation, 'update')

    links_service = request.find_service(name='links')
    group_service = request.find_service(IGroupService)
    resource = AnnotationResource(annotation, group_service, links_service)
    presenter = AnnotationJSONPresenter(resource)
    return presenter.asdict()


@api_config(route_name='api.annotation',
            request_method='DELETE',
            permission='delete',
            link_name='annotation.delete',
            description='Delete an annotation')
def delete(context, request):
    """Delete the specified annotation."""
    storage.delete_annotation(request.db, context.annotation.id)

    # N.B. We publish the original model (including all the original annotation
    # fields) so that queue subscribers have context needed to decide how to
    # process the delete event. For example, the streamer needs to know the
    # target URLs of the deleted annotation in order to know which clients to
    # forward the delete event to.
    _publish_annotation_event(
        request,
        context.annotation,
        'delete')

    return {'id': context.annotation.id, 'deleted': True}


def _json_payload(request):
    """
    Return a parsed JSON payload for the request.

    :raises PayloadError: if the body has no valid JSON body
    """
    try:
        return request.json_body
    except ValueError:
        raise PayloadError()


def _present_annotations(request, ids):
    """Load annotations by id from the database and present them."""
    def eager_load_documents(query):
        return query.options(
            subqueryload(models.Annotation.document))

    annotations = storage.fetch_ordered_annotations(request.db, ids,
                                                    query_processor=eager_load_documents)
    group_service = request.find_service(IGroupService)
    links_service = request.find_service(name='links')
    return [AnnotationJSONPresenter(
                AnnotationResource(ann, group_service, links_service)).asdict()
            for ann in annotations]


def _publish_annotation_event(request,
                              annotation,
                              action):
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


def includeme(config):
    config.scan(__name__)
