# -*- coding: utf-8 -*-

"""HTTP/REST API for interacting with the annotation store."""

import json
import logging

from pyramid.view import view_config

from .auth import get_user
from .models import Annotation
from .resources import Root
from .resources import Annotations

# FixMe: Maybe do conditional import
from ..accounts.models import User
from hem.interfaces import IDBSession
from pyramid_basemodel import Session

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
    # The search results are filtered for the authenticated user
    user = get_user(request)

    nipsa = request.registry.feature('nipsa')
    results = _search(request.params, user)
    if nipsa:
        results = filter_nipsa(request, results, user)

    return results


@api_config(context=Root, name='access_token')
def access_token(request):
    """The OAuth 2 access token view."""
    return request.create_token_response()


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
    user = get_user(request)
    return Annotation.search(user=user)


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
    return annotation


@api_config(context=Annotation, request_method='GET', permission='read')
def read(context, request):
    """Return the annotation (simply how it was stored in the database)."""
    annotation = context

    # Notify any subscribers
    _publish_annotation_event(request, annotation, 'read')

    return annotation


@api_config(context=Annotation, request_method='PUT', permission='update')
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
    return annotation


@api_config(context=Annotation, request_method='DELETE', permission='delete')
def delete(context, request):
    """Delete the annotation permanently."""
    annotation = context
    id = annotation['id']
    # Delete the annotation from the database.
    annotation.delete()

    # Notify any subscribers
    _publish_annotation_event(request, annotation, 'delete')

    # Return a confirmation
    return {
        'id': id,
        'deleted': True,
    }


def _publish_annotation_event(request, annotation, action):
    """Publish an event to the annotations queue for this annotation action"""
    queue = request.get_queue_writer()
    data = {
        'action': action,
        'annotation': annotation,
        'src_client_id': request.headers.get('X-Client-Id'),
    }
    queue.publish('annotations', json.dumps(data))


def _api_error(request, reason, status_code):
    request.response.status_code = status_code
    response_info = {
        'status': 'failure',
        'reason': reason,
    }
    return response_info


def get_nipsa_users(request):
    # FIXME: Add caching
    nipsa_users = User.get_nipsa_users(request)
    return ['acct:' + u + '@' + request.domain for u in nipsa_users]


def filter_nipsa(request, results, user):
    nipsa_users = get_nipsa_users(request)

    total = len(results['rows'])

    # If a flagged user is logged on, then
    # the user can see his/her own annotations
    # So remove the user from the nipsa list
    nipsa_users = [u for u in nipsa_users if user is None or u != user.id]
    results['rows'] = [a for a in results['rows'] if a['user'] not in nipsa_users]
    # FixMe: Update total correctly
    new_total = len(results['rows'])
    results['total'] -= (total - new_total)
    return results


def _search(request_params, user=None):
    # Compile search parameters
    search_params = _search_params(request_params, user=user)

    log.debug("Searching with user=%s, for uri=%s",
              user.id if user else 'None',
              request_params.get('uri'))

    if 'any' in search_params['query']:
        # Handle any field parameters
        query = _add_any_field_params_into_query(search_params)
        results = Annotation.search_raw(query)

        params = {'search_type': 'count'}
        count = Annotation.search_raw(query, params, raw_result=True)
        total = count['hits']['total']
    else:
        results = Annotation.search(**search_params)
        total = Annotation.count(**search_params)

    return {
        'rows': results,
        'total': total,
    }


def _search_params(request_params, user=None):
    """Turn request parameters into annotator-store search parameters."""
    request_params = request_params.copy()
    search_params = {}

    # Take limit, offset, sort and order out of the parameters
    try:
        search_params['offset'] = int(request_params.pop('offset'))
    except (KeyError, ValueError):
        pass
    try:
        search_params['limit'] = int(request_params.pop('limit'))
    except (KeyError, ValueError):
        pass
    try:
        search_params['sort'] = request_params.pop('sort')
    except (KeyError, ValueError):
        pass
    try:
        search_params['order'] = request_params.pop('order')
    except (KeyError, ValueError):
        pass

    # All remaining parameters are considered searched fields.
    search_params['query'] = request_params

    search_params['user'] = user
    return search_params


def _add_any_field_params_into_query(search_params):
    """Add any_field parameters to ES query."""
    any_terms = search_params['query'].getall('any')
    del search_params['query']['any']

    query = search_params.get('query', None)
    offset = search_params.get('offset', None)
    limit = search_params.get('limit', None)
    sort = search_params.get('sort', None)
    order = search_params.get('order', None)
    query = Annotation._build_query(query, offset, limit, sort, order)

    multi_match_query = {
        'multi_match': {
            'query': any_terms,
            'type': 'cross_fields',
            'fields': ['quote', 'tags', 'text', 'uri.parts', 'user']
        }
    }

    # Remove match_all if we add the multi-match part
    if 'match_all' in query['query']['bool']['must'][0]:
        query['query']['bool']['must'] = []
    query['query']['bool']['must'].append(multi_match_query)

    return query


def _create_annotation(fields, user):
    """Create and store an annotation."""

    # Some fields are not to be set by the user, ignore them
    for field in PROTECTED_FIELDS:
        fields.pop(field, None)

    # Create Annotation instance
    annotation = Annotation(fields)

    annotation['user'] = user.id
    annotation['consumer'] = user.consumer.key

    # Save it in the database
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
    registry = config.registry

    if registry.feature('nipsa'):
        if not registry.queryUtility(IDBSession):
            registry.registerUtility(Session, IDBSession)

    config.scan(__name__)
