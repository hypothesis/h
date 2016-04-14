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
objects and Pyramid ACLs in :mod:`h.api.resources`.
"""
import copy

from pyramid import i18n
from pyramid import security
from pyramid.view import view_config

from h.api import cors
from h.api.events import AnnotationEvent
from h.api.presenters import AnnotationJSONPresenter
from h.api.presenters import AnnotationJSONLDPresenter
from h.api import search as search_lib
from h.api import schemas
from h.api import storage

_ = i18n.TranslationStringFactory(__package__)

cors_policy = cors.policy(
    allow_headers=(
        'Authorization',
        'Content-Type',
        'X-Annotator-Auth-Token',
        'X-Client-Id',
    ),
    allow_methods=('HEAD', 'GET', 'POST', 'PUT', 'DELETE'))


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


def api_config(**settings):
    """
    A view configuration decorator with defaults.

    JSON in and out. CORS with tokens and client id but no cookie.
    """
    settings.setdefault('accept', 'application/json')
    settings.setdefault('renderer', 'json')
    settings.setdefault('decorator', cors_policy)
    return view_config(**settings)


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
    # Because request.route_url urlencodes parameters, we can't just pass in
    # ":id" as the id here.
    annotation_url = request.route_url('api.annotation', id='123')\
                            .replace('123', ':id')
    return {
        'message': "Annotator Store API",
        'links': {
            'annotation': {
                'create': {
                    'method': 'POST',
                    'url': request.route_url('api.annotations'),
                    'desc': "Create a new annotation"
                },
                'read': {
                    'method': 'GET',
                    'url': annotation_url,
                    'desc': "Get an existing annotation"
                },
                'update': {
                    'method': 'PUT',
                    'url': annotation_url,
                    'desc': "Update an existing annotation"
                },
                'delete': {
                    'method': 'DELETE',
                    'url': annotation_url,
                    'desc': "Delete an annotation"
                }
            },
            'search': {
                'method': 'GET',
                'url': request.route_url('api.search'),
                'desc': 'Basic search API'
            },
        }
    }


@api_config(route_name='api.search')
def search(request):
    """Search the database for annotations matching with the given query."""
    params = request.params.copy()

    separate_replies = params.pop('_separate_replies', False)
    out = search_lib.search(request,
                            params,
                            separate_replies=separate_replies)

    # Run the results through the JSON presenter
    out['rows'] = [_present_searchdict(request, a)
                   for a in out['rows']]
    if separate_replies:
        out['replies'] = [_present_searchdict(request, a)
                          for a in out['replies']]

    return out


@api_config(route_name='api.annotations',
            request_method='POST',
            effective_principals=security.Authenticated)
def create(request):
    """Create an annotation from the POST payload."""
    json_payload = _json_payload(request)

    # Validate the annotation for, and create the annotation in, PostgreSQL.
    if request.feature('postgres'):
        schema = schemas.CreateAnnotationSchema(request)
        appstruct = schema.validate(copy.deepcopy(json_payload))
        annotation = storage.create_annotation(request, appstruct)

    # Validate the annotation for, and create the annotation in, Elasticsearch.
    legacy_schema = schemas.LegacyCreateAnnotationSchema(request)
    legacy_appstruct = legacy_schema.validate(copy.deepcopy(json_payload))

    # When 'postgres' is on make sure that annotations in the legacy
    # Elasticsearch database use the same IDs as the PostgreSQL ones.
    if request.feature('postgres'):
        assert annotation.id
        legacy_appstruct['id'] = annotation.id

    legacy_annotation = storage.legacy_create_annotation(request,
                                                         legacy_appstruct)

    if request.feature('postgres'):
        _publish_annotation_event(request, annotation, 'create')
        return AnnotationJSONPresenter(request, annotation).asdict()

    _publish_annotation_event(request, legacy_annotation, 'create')
    return AnnotationJSONPresenter(request, legacy_annotation).asdict()


@api_config(route_name='api.annotation', request_method='GET', permission='read')
def read(annotation, request):
    """Return the annotation (simply how it was stored in the database)."""
    presenter = AnnotationJSONPresenter(request, annotation)
    return presenter.asdict()


@api_config(route_name='api.annotation.jsonld',
            request_method='GET',
            permission='read')
def read_jsonld(annotation, request):
    request.response.content_type = 'application/ld+json'
    request.response.content_type_params = {'profile': AnnotationJSONLDPresenter.CONTEXT_URL}
    presenter = AnnotationJSONLDPresenter(request, annotation)
    return presenter.asdict()


@api_config(route_name='api.annotation', request_method='PUT', permission='update')
def update(annotation, request):
    """Update the specified annotation with data from the PUT payload."""
    schema = schemas.LegacyUpdateAnnotationSchema(request,
                                                  annotation=annotation)
    appstruct = schema.validate(_json_payload(request))
    annotation = storage.update_annotation(request, annotation.id, appstruct)

    _publish_annotation_event(request, annotation, 'update')

    presenter = AnnotationJSONPresenter(request, annotation)
    return presenter.asdict()


@api_config(route_name='api.annotation', request_method='DELETE', permission='delete')
def delete(annotation, request):
    """Delete the specified annotation."""
    storage.delete_annotation(request, annotation.id)

    # N.B. We publish the original model (including all the original annotation
    # fields) so that queue subscribers have context needed to decide how to
    # process the delete event. For example, the streamer needs to know the
    # target URLs of the deleted annotation in order to know which clients to
    # forward the delete event to.
    _publish_annotation_event(
        request,
        annotation,
        'delete')

    return {'id': annotation.id, 'deleted': True}


def _json_payload(request):
    """
    Return a parsed JSON payload for the request.

    :raises PayloadError: if the body has no valid JSON body
    """
    try:
        return request.json_body
    except ValueError:
        raise PayloadError()


def _present_searchdict(request, mapping):
    """Run an object returned from search through a presenter."""
    ann = storage.annotation_from_dict(mapping)
    return AnnotationJSONPresenter(request, ann).asdict()


def _publish_annotation_event(request, annotation, action):
    """Publish an event to the annotations queue for this annotation action"""
    event = AnnotationEvent(request, annotation, action)
    request.registry.notify(event)


def includeme(config):
    config.scan(__name__)
    config.add_subscriber('h.api.subscribers.index_annotation_event',
                          'h.api.events.AnnotationEvent')
