# -*- coding: utf-8 -*-

"""HTTP/REST API for interacting with the annotation store."""

import logging

from pyramid.view import view_config

from h.api import search as search_lib
from h.api.auth import get_user
from h.api.events import AnnotationEvent
from h.api.models import Annotation
from h.api.resources import Root
from h.api.resources import Annotations
from h.api import nipsa


log = logging.getLogger(__name__)


# These annotation fields are not to be set by the user.
PROTECTED_FIELDS = ['created', 'updated', 'user', 'consumer', 'id']


def api_config(**kwargs):
    """Extend Pyramid's @view_config decorator with modified defaults."""
    config = {
        'accept': 'application/json',
        'renderer': 'json',
    }
    config.update(kwargs)
    return view_config(**config)


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
    search_normalized_uris = request.feature('search_normalized')

    # The search results are filtered for the authenticated user
    user = get_user(request)
    results = search_lib.search(request.params,
                                user=user,
                                search_normalized_uris=search_normalized_uris)

    return {
        'total': results['total'],
        'rows': [search_lib.render(a) for a in results['rows']],
    }


@api_config(context=Root, name='access_token')
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
@api_config(context=Root, name='token', renderer='string')
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
    search_normalized_uris = request.feature('search_normalized')

    user = get_user(request)
    results = search_lib.index(user=user,
                               search_normalized_uris=search_normalized_uris)

    return {
        'total': results['total'],
        'rows': [search_lib.render(a) for a in results['rows']],
    }


@api_config(context=Annotations, request_method='POST', permission='create')
def create(request):
    """Read the POSTed JSON-encoded annotation and persist it."""
    user = get_user(request)

    # Read the annotation from the request payload
    try:
        fields = request.json_body
    except ValueError:
        return _api_error(request,
                          'No JSON payload sent. Annotation not created.',
                          status_code=400)  # Client Error: Bad Request

    # Create the annotation
    annotation = _create_annotation(fields, user)

    # Notify any subscribers
    _publish_annotation_event(request, annotation, 'create')

    # Return it so the client gets to know its ID and such
    return search_lib.render(annotation)


@api_config(containment=Root, context=Annotation,
            request_method='GET', permission='read')
def read(context, request):
    """Return the annotation (simply how it was stored in the database)."""
    annotation = context

    # Notify any subscribers
    _publish_annotation_event(request, annotation, 'read')

    return search_lib.render(annotation)


@api_config(containment=Root, context=Annotation,
            request_method='PUT', permission='update')
def update(context, request):
    """Update the fields we received and store the updated version."""
    annotation = context

    # Read the new fields for the annotation
    try:
        fields = request.json_body
    except ValueError:
        return _api_error(request,
                          'No JSON payload sent. Annotation not created.',
                          status_code=400)  # Client Error: Bad Request

    # Check user's permissions
    has_admin_permission = request.has_permission('admin', annotation)

    # Update and store the annotation
    try:
        _update_annotation(annotation, fields, has_admin_permission)
    except RuntimeError as err:
        return _api_error(
            request,
            err.args[0],
            status_code=err.args[1])

    # Notify any subscribers
    _publish_annotation_event(request, annotation, 'update')

    # Return the updated version that was just stored.
    return search_lib.render(annotation)


@api_config(containment=Root, context=Annotation,
            request_method='DELETE', permission='delete')
def delete(context, request):
    """Delete the annotation permanently."""
    annotation = context
    id_ = annotation['id']
    # Delete the annotation from the database.
    annotation.delete()

    # Notify any subscribers
    _publish_annotation_event(request, annotation, 'delete')

    # Return a confirmation
    return {
        'id': id_,
        'deleted': True,
    }


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


def _create_annotation(fields, user):
    """Create and store an annotation."""

    # Some fields are not to be set by the user, ignore them
    for field in PROTECTED_FIELDS:
        fields.pop(field, None)

    # Create Annotation instance
    annotation = Annotation(fields)

    annotation['user'] = user.id
    annotation['consumer'] = user.consumer.key

    if nipsa.has_nipsa(user.id):
        annotation["nipsa"] = True

    # Save it in the database
    search_lib.prepare(annotation)
    annotation.save()

    log.debug('Created annotation; user: %s, consumer key: %s',
              annotation['user'], annotation['consumer'])

    return annotation


def _update_annotation(annotation, fields, has_admin_permission):
    # Some fields are not to be set by the user, ignore them
    for field in PROTECTED_FIELDS:
        fields.pop(field, None)

    # If the user is changing access permissions, check if it's allowed.
    changing_permissions = (
        'permissions' in fields and
        fields['permissions'] != annotation.get('permissions', {})
    )
    if changing_permissions and not has_admin_permission:
        raise RuntimeError("Not authorized to change annotation permissions.",
                           401)  # Unauthorized

    # Update the annotation with the new data
    annotation.update(fields)

    # If the annotation is flagged as deleted, remove mentions of the user
    if annotation.get('deleted', False):
        _anonymize_deletes(annotation)

    # Save the annotation in the database, overwriting the old version.
    search_lib.prepare(annotation)
    annotation.save()


def _anonymize_deletes(annotation):
    """Clear the author and remove the user from the annotation permissions."""

    # Delete the annotation author, if present
    user = annotation.pop('user')

    # Remove the user from the permissions, but keep any others in place.
    permissions = annotation.get('permissions', {})
    for action in permissions.keys():
        filtered = [
            role
            for role in annotation['permissions'][action]
            if role != user
        ]
        annotation['permissions'][action] = filtered


def includeme(config):
    config.scan(__name__)
