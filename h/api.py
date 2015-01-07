# -*- coding: utf-8 -*-

"""HTTP/REST API for interacting with the annotation store."""

import logging
import time

from annotator import auth, es
from elasticsearch import exceptions as elasticsearch_exceptions
from pyramid.renderers import JSON
from pyramid.settings import asbool
from pyramid.view import view_config

from h import authorization, events
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
    return _search(request.params, user)


@api_config(context='h.resources.APIResource', name='access_token')
def access_token(context, request):
    """The OAuth 2 access token view."""
    if request.grant_type is None:
        request.grant_type = 'client_credentials'
    return request.create_token_response()


@api_config(context='h.resources.APIResource', name='token', renderer='string')
def annotator_token(context, request):
    """The Annotator Auth token view."""
    return authorization.token_generator(request)


@api_config(context='h.resources.AnnotationFactory', request_method='GET')
def annotations_index(context, request):
    """Do a search for all annotations on anything and return results.

    This will use the default limit, 20 at time of writing, and results
    are ordered most recent first.
    """
    user = get_user(request)
    return Annotation.search(user=user)


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
        consumer = auth.Consumer(request.client.client_id)
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


def _search(request_params, user = None):
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


def _add_any_field_params_into_query(search_params):
    """Add any_field parameters to ES query"""
    any_terms = search_params['query'].getall('any')
    del search_params['query']['any']

    offset = search_params.get('offset', None)
    limit = search_params.get('limit', None)
    query = Annotation._build_query(search_params['query'], offset, limit)

    multi_match_query = {
        'multi_match': {
            'query': any_terms,
            'type': 'cross_fields',
            'fields': ['quote', 'tags', 'text', 'uri', 'user']
        }
    }

    # Remove match_all if we add the multi-match part
    if 'match_all' in query['query']['bool']['must'][0]:
        query['query']['bool']['must'] = []
    query['query']['bool']['must'].append(multi_match_query)

    return query


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

    return es


def _ensure_es_plugins(es_conn):
    """Ensure that the ICU analysis plugin is installed for ES"""
    # Pylint issue #258: https://bitbucket.org/logilab/pylint/issue/258
    #
    # pylint: disable=unexpected-keyword-arg
    names = [x.strip() for x in es_conn.cat.plugins(h='component').split('\n')]
    if 'analysis-icu' not in names:
        message = ("ICU Analysis plugin is not installed for ElasticSearch\n"
                   "  See the installation instructions for more details:\n"
                   "  https://github.com/hypothesis/h/blob/master/"
                   "INSTALL.rst#installing")
        raise RuntimeError(message)


def create_db():
    """Create the ElasticSearch index for Annotations and Documents"""
    # Check for required plugin(s)
    _ensure_es_plugins(es.conn)

    models = [Annotation, Document]
    mappings = {}
    analysis = {}

    # Collect the mappings and analysis settings
    for model in models:
        mappings.update(model.get_mapping())
        for section, items in model.get_analysis().items():
            existing_items = analysis.setdefault(section, {})
            for name in items:
                if name in existing_items:
                    fmt = "Duplicate definition of 'index.analysis.{}.{}'."
                    msg = fmt.format(section, name)
                    raise RuntimeError(msg)
            existing_items.update(items)

    # Create the index
    try:
        # Pylint issue #258: https://bitbucket.org/logilab/pylint/issue/258
        #
        # pylint: disable=unexpected-keyword-arg
        response = es.conn.indices.create(es.index, ignore=400, body={
            'mappings': mappings,
            'settings': {'analysis': analysis},
        })
    except elasticsearch_exceptions.ConnectionError as e:
        msg = ('Can not access ElasticSearch at {0}! '
               'Check to ensure it is running.').format(es.host)
        raise elasticsearch_exceptions.ConnectionError('N/A', msg, e)

    # Bad request (400) is ignored above, to prevent warnings in the log, but
    # the failure could be for reasons other than that the index exists. If so,
    # raise the error here.
    if 'error' in response and 'IndexAlreadyExists' not in response['error']:
        raise elasticsearch_exceptions.RequestError(400, response['error'])

    # Update analysis settings
    settings = es.conn.indices.get_settings(index=es.index)
    existing = settings[es.index]['settings']['index'].get('analysis', {})
    if existing != analysis:
        try:
            es.conn.indices.close(index=es.index)
            es.conn.indices.put_settings(index=es.index, body={
                'analysis': analysis
            })
        finally:
            es.conn.indices.open(index=es.index)

    # Update mappings
    try:
        for doc_type, body in mappings.items():
            es.conn.indices.put_mapping(
                index=es.index,
                doc_type=doc_type,
                body=body
            )
    except elasticsearch_exceptions.RequestError as e:
        if e.error.startswith('MergeMappingException'):
            date = time.strftime('%Y-%m-%d')
            message = ("Elasticsearch index mapping is incorrect! Please "
                       "reindex it. For example, run: "
                       "./bin/hypothesis reindex {0} {1} {1}-{2}"
                       .format('yourconfig.ini', es.index, date)
                       )
            log.critical(message)
            raise RuntimeError(message)
        raise


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
