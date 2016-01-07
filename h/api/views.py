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

import logging

from pyramid import httpexceptions
from pyramid import i18n
from pyramid.view import forbidden_view_config, notfound_view_config
from pyramid.view import view_config

from h.api import cors
from h.api.events import AnnotationEvent
from h.api import search as search_lib
from h.api import schemas
from h.api import storage
from h.api.resources import Annotation
from h.api.resources import Annotations
from h.api.resources import Root

_ = i18n.TranslationStringFactory(__package__)

log = logging.getLogger(__name__)

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


def json_view(**settings):
    """A view configuration decorator with JSON defaults."""
    settings.setdefault('accept', 'application/json')
    settings.setdefault('renderer', 'json')
    return view_config(**settings)


def api_config(**settings):
    """
    A view configuration decorator with defaults.

    JSON in and out. CORS with tokens and client id but no cookie.
    """
    settings.setdefault('decorator', cors_policy)
    return json_view(**settings)


@forbidden_view_config(containment=Root, renderer='json')
@notfound_view_config(containment=Root, renderer='json')
def error_not_found(context, request):
    request.response.status_code = httpexceptions.HTTPNotFound.code
    return {'status': 'failure', 'reason': 'not_found'}


@api_config(context=APIError)
def error_api(context, request):
    request.response.status_code = context.status_code
    return {'status': 'failure', 'reason': context.message}


@api_config(context=schemas.ValidationError)
def error_validation(context, request):
    request.response.status_code = 400
    return {'status': 'failure', 'reason': context.message}


@api_config(context=Root)
@api_config(route_name='api')
def index(context, request):
    """Return the API descriptor document.

    Clients may use this to discover endpoints for the API.
    """
    return {
        'message': "Annotator Store API",
        'links': {
            'annotation': {
                'create': {
                    'method': 'POST',
                    'url': request.resource_url(context, 'annotations'),
                    'desc': "Create a new annotation"
                },
                'read': {
                    'method': 'GET',
                    'url': request.resource_url(context, 'annotations', ':id'),
                    'desc': "Get an existing annotation"
                },
                'update': {
                    'method': 'PUT',
                    'url': request.resource_url(context, 'annotations', ':id'),
                    'desc': "Update an existing annotation"
                },
                'delete': {
                    'method': 'DELETE',
                    'url': request.resource_url(context, 'annotations', ':id'),
                    'desc': "Delete an annotation"
                }
            },
            'search': {
                'method': 'GET',
                'url': request.resource_url(context, 'search'),
                'desc': 'Basic search API'
            },
        }
    }


@api_config(context=Root, name='search')
def search(request):
    """Search the database for annotations matching with the given query."""
    params = request.params.copy()

    separate_replies = params.pop('_separate_replies', False)
    return search_lib.search(request,
                             params,
                             separate_replies=separate_replies)


@api_config(route_name='access_token')
def access_token(request):
    """The OAuth 2 access token view."""
    return request.create_token_response()


# N.B. Like the rest of the API, this view is exposed behind WSGI middleware
# that enables appropriate CORS headers and response to preflight request.
#
# However, this view requires credentials (a cookie) so is in fact not
# currently accessible off-origin. Given that this method of authenticating to
# the API is not intended to remain, this seems like a limitation we do not
# need to lift any time soon.
@api_config(route_name='token', renderer='string')
def annotator_token(request):
    """The Annotator Auth token view."""
    request.grant_type = 'client_credentials'
    response = access_token(request)
    return response.json_body.get('access_token', response)


@api_config(context=Annotations, request_method='GET')
def annotations_index(request):
    """Do a search for all annotations on anything and return results.

    This will use the default limit, 20 at time of writing, and results
    are ordered most recent first.
    """
    return search_lib.search(request, {"limit": 20})


@api_config(context=Annotations, request_method='POST', permission='create')
def create(request):
    """Create an annotation from the POST payload."""
    schema = schemas.CreateAnnotationSchema(request)
    appstruct = schema.validate(_json_payload(request))
    annotation = storage.create_annotation(appstruct)

    _publish_annotation_event(request, annotation, 'create')
    return annotation


@api_config(context=Annotation, request_method='GET', permission='read')
def read(context, request):
    """Return the annotation (simply how it was stored in the database)."""
    return context.model


@api_config(context=Annotation, request_method='PUT', permission='update')
def update(context, request):
    """Update the specified annotation with data from the PUT payload."""
    schema = schemas.UpdateAnnotationSchema(request, annotation=context.model)
    appstruct = schema.validate(_json_payload(request))
    annotation = storage.update_annotation(context.id, appstruct)

    _publish_annotation_event(request, annotation, 'update')
    return annotation


@api_config(context=Annotation, request_method='DELETE', permission='delete')
def delete(context, request):
    """Delete the specified annotation."""
    storage.delete_annotation(context.id)

    _publish_annotation_event(request, {'id': context.id}, 'delete')
    return {'id': context.id, 'deleted': True}


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
    """Publish an event to the annotations queue for this annotation action"""
    event = AnnotationEvent(request, annotation, action)
    request.registry.notify(event)


def includeme(config):
    config.scan(__name__)
