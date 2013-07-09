try:
    import simplejson as json
except ImportError:
    import json

import re

import flask

from annotator import auth, authz, store, es
from annotator.annotation import Annotation

from pyramid.request import Request
from pyramid.threadlocal import get_current_registry
from pyramid.wsgi import wsgiapp2

from h import api, events, interfaces, models

import logging
log = logging.getLogger(__name__)


class Store(object):
    def __init__(self, request):
        self.request = request

    @property
    def base_url(self):
        """The base URL of the store.

        This is the URL of the service document.
        """
        return self.request.route_url('api', subpath='')

    def create(self):
        raise NotImplementedError()

    def read(self, key):
        url = self.request.route_url('api', subpath='annotations/%s' % key)
        subreq = Request.blank(url)
        return self._invoke_subrequest(subreq).json

    def update(self, key, data):
        raise NotImplementedError()

    def delete(self, key):
        raise NotImplementedError()

    def search(self, **query):
        url = self.request.route_url('api', subpath='search', _query=query)
        subreq = Request.blank(url)
        return self._invoke_subrequest(subreq).json['rows']

    def search_raw(self, query):
        url = self.request.route_url('api', subpath='search_raw')
        subreq = Request.blank(url, method='POST')
        subreq.json = query
        result = self._invoke_subrequest(subreq)
        payload = json.loads(result.body)

        hits = []
        for res in payload['hits']['hits']:
            hits.append(res["_source"])
        return hits

    def _invoke_subrequest(self, subreq):
        request = self.request
        token = api.TokenController(request)()
        subreq.headers['X-Annotator-Auth-Token'] = token
        return request.invoke_subrequest(subreq)


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
    action_field = annotation.get('permissions', {}).get(action, [])

    if not action_field:
        return True
    else:
        return authz.authorize(annotation, action, user)


def before_request():
    flask.g.auth = auth.Authenticator(models.Consumer.get_by_key)
    flask.g.authorize = authorize
    flask.g.before_annotation_update = anonymize_deletes


def after_request(response):
    if 200 <= response.status_code < 300:
        match = re.match(r'^store\.(\w+)_annotation$', flask.request.endpoint)
        if match:
            action = match.group(1)
            if action != 'delete':
                annotation = json.loads(response.data)
                event = events.AnnotatorStoreEvent(annotation, action)
                get_current_registry().notify(event)
    return response


def includeme(config):
    app = flask.Flask('annotator')  # Create the annotator-store app
    app.register_blueprint(store.store)  # and register the store api.
    settings = config.get_settings()

    if 'es.host' in settings:
        app.config['ELASTICSEARCH_HOST'] = settings['es.host']
    if 'es.index' in settings:
        app.config['ELASTICSEARCH_INDEX'] = settings['es.index']
    es.init_app(app)
    with app.test_request_context():
        Annotation.create_all()

    # Configure authentication and authorization
    app.config['AUTHZ_ON'] = True
    app.before_request(before_request)
    app.after_request(after_request)

    # Configure the API views -- version 1 is just an annotator.store proxy
    api_v1 = wsgiapp2(app)

    config.add_view(api_v1, route_name='api')

    if not config.registry.queryUtility(interfaces.IStoreClass):
        config.registry.registerUtility(Store, interfaces.IStoreClass)
