# -*- coding: utf-8 -*-
import json
import logging
import os
import re
import socket

from annotator import auth, store, es
import flask
from pyramid.httpexceptions import exception_response
from pyramid.request import Request
from pyramid.threadlocal import get_current_request
from pyramid.wsgi import wsgiapp2

from h import api, events, interfaces, models

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Store(object):
    def __init__(self, request):
        self.request = request

    def create(self):
        raise NotImplementedError()

    def read(self, key):
        url = self.request.route_url('api_real',
                                     subpath='annotations/%s' % key)
        subreq = Request.blank(url)
        return self._invoke_subrequest(subreq).json

    def update(self, key, data):
        raise NotImplementedError()

    def delete(self, key):
        raise NotImplementedError()

    def search(self, **query):
        url = self.request.route_url('api_real', subpath='search',
                                     _query=query)
        subreq = Request.blank(url)
        return self._invoke_subrequest(subreq).json['rows']

    def search_raw(self, query):
        url = self.request.route_url('api_real', subpath='search_raw')
        subreq = Request.blank(url, method='POST')
        subreq.json = query
        result = self._invoke_subrequest(subreq)
        payload = json.loads(result.body)

        hits = []
        for res in payload['hits']['hits']:
            # Add id
            res["_source"]["id"] = res["_id"]
            hits.append(res["_source"])
        return hits

    def _invoke_subrequest(self, subreq):
        request = self.request
        # XXX: This should be available more easily somewhere like the session.
        token = api.token.TokenController(request)()
        subreq.headers['X-Annotator-Auth-Token'] = token
        result = request.invoke_subrequest(subreq)

        if result.status_int > 400:
            raise exception_response(result.status_int)

        return result


def wrap_annotation(annotation):
    """Wraps a dict as an instance of the registered Annotation model class.

    Arguments:
    - `annotation`: a dictionary-like object containing the model data
    """

    request = get_current_request()
    cls = request.registry.queryUtility(interfaces.IAnnotationClass)
    result = cls(request)
    result.update(annotation)
    return result


def anonymize_deletes(annotation):
    if annotation.get('deleted', False):
        user = annotation.get('user', '')
        if user:
            annotation['user'] = ''

        permissions = annotation.get('permissions', {})
        for action in permissions.keys():
            filtered = [
                role
                for role in annotation['permissions'][action]
                if role != user
            ]
            annotation['permissions'][action] = filtered


def authorize(annotation, action, user=None):
    request = get_current_request()
    annotation = wrap_annotation(annotation)

    result = request.has_permission(action, annotation)
    if not result:
        print result
    return result


def before_request():
    flask.g.annotation_class = models.Annotation
    flask.g.auth = auth.Authenticator(models.Consumer.get_by_key)
    flask.g.authorize = authorize
    flask.g.before_annotation_update = anonymize_deletes


def after_request(response):
    if flask.request.method == 'OPTIONS':
        in_value = response.headers.get('Access-Control-Allow-Headers', '')
        allowed = [h.strip() for h in in_value.split(',')]
        allowed.append('X-Client-ID')
        out_value = ', '.join(allowed)
        response.headers['Access-Control-Allow-Headers'] = out_value
        return response

    if 200 <= response.status_code < 300:
        match = re.match(r'^store\.(\w+)_annotation$', flask.request.endpoint)
        if match:
            request = get_current_request()

            action = match.group(1)
            if action == 'delete':
                data = json.loads(flask.request.data)
            else:
                data = json.loads(response.data)

            annotation = wrap_annotation(data)
            event = events.AnnotationEvent(request, annotation, action)

            request.registry.notify(event)
    return response


def store_from_settings(settings):
    app = flask.Flask('annotator')  # Create the annotator-store app
    app.register_blueprint(store.store)  # and register the store api.

    if 'ELASTICSEARCH_PORT' in os.environ:
        app.config['ELASTICSEARCH_HOST'] = 'http%s' % (
            os.environ['ELASTICSEARCH_PORT'][3:],
        )
    elif 'es.host' in settings:
        app.config['ELASTICSEARCH_HOST'] = settings['es.host']

    if 'es.index' in settings:
        app.config['ELASTICSEARCH_INDEX'] = settings['es.index']

    if 'es.compatibility' in settings:
        compat = settings['es.compatibility']
        app.config['ELASTICSEARCH_COMPATIBILITY_MODE'] = compat

    es.init_app(app)
    return app


def create_db(app):
    try:
        with app.test_request_context():
            # pylint: disable=no-member
            models.Annotation.create_all()
            models.Document.create_all()
    except socket.error:
        raise Exception(
            "Can not access ElasticSearch at %s! Are you sure it's running?" %
            (app.config["ELASTICSEARCH_HOST"],)
        )
    except:
        with app.test_request_context():
            # pylint: disable=no-member
            models.Annotation.update_settings()
            models.Annotation.create_all()
            models.Document.create_all()


def includeme(config):
    """Include the annotator-store API backend via http or route embedding.

    Example INI file:
    .. code-block:: ini
        [app:h]
        api.key: 00000000-0000-0000-0000-000000000000
        api.endpoint: https://example.com/api

    or use a relative path for the endpoint to embed the annotation store
    directly in the application.
    .. code-block:: ini
        [app:h]
        api.endpoint: /api

    The default is to embed the store as a route bound to "/api".
    """
    app = store_from_settings(config.registry.settings)

    # Configure authentication and authorization
    app.config['AUTHZ_ON'] = True
    app.before_request(before_request)
    app.after_request(after_request)

    # Configure the API routes
    api_endpoint = config.registry.settings.get('api.endpoint', None)
    api_url = config.registry.settings.get('api.url', api_endpoint)

    if api_endpoint is not None:
        api_path = api_endpoint.rstrip('/')
        api_pattern = '/'.join([api_path, '*subpath'])

        # Configure the API views -- version 1 is just an annotator.store proxy
        api_v1 = wsgiapp2(app)

        config.add_route('api_real', api_pattern)
        config.add_view(api_v1, route_name='api_real')
        config.add_view(api_v1, name='api_virtual')

    if api_url is not None:
        api_url = api_url.strip('/')
        config.add_route('api', api_url + '/*subpath')

    if not config.registry.queryUtility(interfaces.IStoreClass):
        config.registry.registerUtility(Store, interfaces.IStoreClass)
