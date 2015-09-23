# -*- coding: utf-8 -*-

"""HTTP/REST API for interacting with the annotation store."""

import logging

from pyramid import httpexceptions
from pyramid.view import forbidden_view_config, notfound_view_config
from pyramid.view import view_config

from h.api import cors
from h.api.events import AnnotationEvent
from h.api import search as search_lib
from h.api import logic
from h.api.resources import Annotation
from h.api.resources import Annotations
from h.api.resources import Root


log = logging.getLogger(__name__)


cors_policy = cors.policy(
    allow_headers=(
        'Authorization',
        'Content-Type',
        'X-Annotator-Auth-Token',
        'X-Client-Id',
    ),
    allow_methods=('HEAD', 'GET', 'POST', 'PUT', 'DELETE'))


def api_config(**settings):
    """
    A view configuration decorator with defaults.

    JSON in and out. CORS with tokens and client id but no cookie.
    """
    settings.setdefault('decorator', cors_policy)
    return json_view(**settings)


def json_view(**settings):
    """A view configuration decorator with JSON defaults."""
    settings.setdefault('accept', 'application/json')
    settings.setdefault('renderer', 'json')
    return view_config(**settings)


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
    results = search_lib.search(request, request.params)

    return {
        'total': results['total'],
        'rows': [search_lib.render(a) for a in results['rows']],
    }


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
    results = search_lib.search(request, {"limit": 20})

    return {
        'total': results['total'],
        'rows': [search_lib.render(a) for a in results['rows']],
    }


@api_config(context=Annotations, request_method='POST', permission='create')
def create(request):
    """Read the POSTed JSON-encoded annotation and persist it."""
    # Read the annotation from the request payload
    try:
        fields = request.json_body
    except ValueError:
        return _api_error(request,
                          'No JSON payload sent. Annotation not created.',
                          status_code=400)  # Client Error: Bad Request

    # Create the annotation
    user = request.authenticated_userid
    annotation = logic.create_annotation(fields, user)

    # Notify any subscribers
    _publish_annotation_event(request, annotation, 'create')

    # Return it so the client gets to know its ID and such
    return search_lib.render(annotation)


@api_config(context=Annotation, request_method='GET', permission='read')
def read(context, request):
    """Return the annotation (simply how it was stored in the database)."""
    annotation = context.model

    # Notify any subscribers
    _publish_annotation_event(request, annotation, 'read')

    return search_lib.render(annotation)


@api_config(context=Annotation, request_method='PUT', permission='update')
def update(context, request):
    """Update the fields we received and store the updated version."""
    annotation = context.model

    # Read the new fields for the annotation
    try:
        fields = request.json_body
    except ValueError:
        return _api_error(request,
                          'No JSON payload sent. Annotation not created.',
                          status_code=400)  # Client Error: Bad Request

    # Update and store the annotation
    user = request.authenticated_userid

    try:
        logic.update_annotation(annotation, fields, user)
    except RuntimeError as err:
        return _api_error(
            request,
            err.args[0],
            status_code=err.args[1])

    # Notify any subscribers
    _publish_annotation_event(request, annotation, 'update')

    # Return the updated version that was just stored.
    return search_lib.render(annotation)


@api_config(context=Annotation, request_method='DELETE', permission='delete')
def delete(context, request):
    """Delete the annotation permanently."""
    annotation = context.model

    logic.delete_annotation(annotation)

    # Notify any subscribers
    _publish_annotation_event(request, annotation, 'delete')

    # Return a confirmation
    return {
        'id': annotation['id'],
        'deleted': True,
    }


@forbidden_view_config(containment=Root, renderer='json')
@notfound_view_config(containment=Root, renderer='json')
def notfound(context, request):
    request.response.status_int = httpexceptions.HTTPNotFound.code
    return {'status': 'failure', 'reason': 'not_found'}


def _publish_annotation_event(request, annotation, action):
    """Publish an event to the annotations queue for this annotation action"""
    event = AnnotationEvent(request, annotation, action)
    request.registry.notify(event)


def _api_error(request, reason, status_code):
    request.response.status_code = status_code
    response_info = {
        'status': 'failure',
        'reason': reason,
    }
    return response_info


def includeme(config):
    config.scan(__name__)
