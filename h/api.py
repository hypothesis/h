# -*- coding: utf-8 -*-

"""HTTP/REST API for interacting with the annotation store."""

import logging

from annotator import auth, es
from elasticsearch import exceptions as elasticsearch_exceptions
from pyramid.renderers import JSON
from pyramid.settings import asbool
from pyramid.view import view_config

from h import events
from h.models import Annotation, Document


log = logging.getLogger(__name__)


# These annotation fields are not to be set by the user.
PROTECTED_FIELDS = ['created', 'updated', 'user', 'consumer', 'id']


def api_config(**kwargs):
    """Pyramid's @view_config decorator but with modified defaults"""
    config = {
        # The containment predicate ensures we only respond to API calls
        'containment': 'h.resources.APIResource',
        'accept': 'application/json',
        'renderer': 'json',
    }
    config.update(kwargs)
    return view_config(**config)


@api_config(context='h.resources.APIResource')
@api_config(context='h.resources.APIResource', route_name='index')
def index(context, request):
    """Return the API descriptor document

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


@api_config(context='h.resources.APIResource', name='search')
def search(context, request):
    """Search the database for annotations matching with the given query."""

    # The search results are filtered for the authenticated user
    user = get_user(request)

    # Compile search parameters
    search_params = _search_params(request.params, user=user)
    search_params['query']['consumer'] = request.consumer.client_id

    log.debug("Searching with user=%s, for uri=%s",
              user.id if user else 'None',
              search_params.get('uri'))

    results = Annotation.search(**search_params)
    total = Annotation.count(**search_params)

    return {
        'rows': results,
        'total': total,
    }


@api_config(context='h.resources.APIResource',
            name='access_token',
            renderer='json')
def access_token(context, request):
    """The OAuth 2 access token view."""
    if request.grant_type is None:
        request.grant_type = 'client_credentials'
    return request.create_token_response()


@api_config(context='h.resources.APIResource', name='token', renderer='string')
def annotator_token(context, request):
    """The Annotator Auth token view."""
    response = access_token(context, request)
    return response.json_body.get('access_token', response)


@api_config(context='h.resources.AnnotationFactory', request_method='GET')
def annotations_index(context, request):
    """Do a search for all annotations on anything and return results.

    This will use the default limit, 20 at time of writing, and results
    are ordered most recent first.
    """
    user = get_user(request)
    query = dict(consumer=request.consumer.client_id)
    return Annotation.search(user=user, query=query)


@api_config(context='h.resources.AnnotationFactory',
            request_method='POST',
            permission='create')
def create(context, request):
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
    _trigger_event(request, annotation, 'create')

    # Return it so the client gets to know its ID and such
    return annotation


@api_config(context='h.models.Annotation',
            request_method='GET',
            permission='read')
def read(context, request):
    """Return the annotation (simply how it was stored in the database)"""
    annotation = context

    # Notify any subscribers
    _trigger_event(request, annotation, 'read')

    return annotation


@api_config(context='h.models.Annotation',
            request_method='PUT',
            permission='update')
def update(context, request):
    """Update the fields we received and store the updated version"""
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
    _trigger_event(request, annotation, 'update')

    # Return the updated version that was just stored.
    return annotation


@api_config(context='h.models.Annotation',
            request_method='DELETE',
            permission='delete')
def delete(context, request):
    """Delete the annotation permanently."""
    annotation = context
    id = annotation['id']
    # Delete the annotation from the database.
    annotation.delete()

    # Notify any subscribers
    _trigger_event(request, annotation, 'delete')

    # Return a confirmation
    return {
        'id': id,
        'deleted': True,
    }


def get_user(request):
    """Create a User object for annotator-store"""
    userid = request.authenticated_userid
    if userid is not None:
        consumer = auth.Consumer(request.consumer.client_id)
        return auth.User(userid, consumer, False)
    return None


def _trigger_event(request, annotation, action):
    """Trigger any callback functions listening for AnnotationEvents"""
    event = events.AnnotationEvent(request, annotation, action)
    request.registry.notify(event)


def _api_error(request, reason, status_code):
    request.response.status_code = status_code
    response_info = {
        'status': 'failure',
        'reason': reason,
    }
    return response_info


def _search_params(request_params, user=None):
    """Turn request parameters into annotator-store search parameters"""
    request_params = request_params.copy()
    search_params = {}

    # Take limit and offset out of the parameters
    try:
        search_params['offset'] = int(request_params.pop('offset'))
    except (KeyError, ValueError):
        pass
    try:
        search_params['limit'] = int(request_params.pop('limit'))
    except (KeyError, ValueError):
        pass

    # All remaining parameters are considered searched fields.
    search_params['query'] = request_params

    search_params['user'] = user
    return search_params


def _create_annotation(fields, user):
    """Create and store an annotation"""

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
        'permissions' in fields
        and fields['permissions'] != annotation.get('permissions', {})
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
    """Clear the author and remove the user from the annotation permissions"""

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


def store_from_settings(settings):
    """Configure the Elasticsearch wrapper provided by annotator-store"""
    if 'es.host' in settings:
        es.host = settings['es.host']

    if 'es.index' in settings:
        es.index = settings['es.index']

    if 'es.compatibility' in settings:
        es.compatibility_mode = settings['es.compatibility']

    # We want search results to be filtered according to their
    # read-permissions, which is done in the store itself.
    es.authorization_enabled = True

    # Note that we do not have to actually open the database connection or
    # anything, annotator-store will do so on the first invoked action.
    return es


def create_db():
    """Create the ElasticSearch index for Annotations and Documents"""
    try:
        es.conn.indices.create(es.index)
    except elasticsearch_exceptions.RequestError as e:
        if not (e.error.startswith('IndexAlreadyExistsException')
                or e.error.startswith('InvalidIndexNameException')):
            raise
    except elasticsearch_exceptions.ConnectionError as e:
        msg = ('Can not access ElasticSearch at {0}! '
               'Check to ensure it is running.').format(es.host)
        raise elasticsearch_exceptions.ConnectionError('N/A', msg, e)
    # Pylint issue #258: https://bitbucket.org/logilab/pylint/issue/258
    #
    # pylint: disable=unexpected-keyword-arg
    es.conn.cluster.health(wait_for_status='yellow')
    # pylint: enable=unexpected-keyword-arg
    Annotation.update_settings()
    Annotation.create_all()
    Document.create_all()


def delete_db():
    Annotation.drop_all()
    Document.drop_all()


def includeme(config):
    registry = config.registry
    settings = registry.settings

    config.add_renderer('json', JSON(indent=4))

    # Configure ElasticSearch
    store_from_settings(settings)

    # Maybe initialize the models
    if asbool(settings.get('basemodel.should_drop_all', False)):
        delete_db()
    if asbool(settings.get('basemodel.should_create_all', True)):
        create_db()

    config.scan(__name__)
