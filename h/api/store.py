from annotator import auth, authz, store, es
from annotator.annotation import Annotation

from flask import Flask, g

from pyramid.request import Request
from pyramid.wsgi import wsgiapp2

from h import models


class Store(object):
    def __init__(self, request):
        self.request = request

    def create(self):
        raise NotImplementedError()

    def read(self, key):
        url = self.request.route_url('api', subpath='annotations/%s' % key)
        subreq = Request.blank(url)
        return self.request.invoke_subrequest(subreq).json

    def update(self, key, data):
        raise NotImplementedError()

    def delete(self, key):
        raise NotImplementedError()

    def search(self, **query):
        url = self.request.route_url('api', subpath='search', _query=query)
        subreq = Request.blank(url)
        return self.request.invoke_subrequest(subreq).json['rows']


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
    g.auth = auth.Authenticator(models.Consumer.get_by_key)
    g.authorize = authorize
    g.before_annotation_update = anonymize_deletes


def includeme(config):
    app = Flask('annotator')  # Create the annotator-store app
    app.register_blueprint(store.store)  # and register the store api.

    # Set up the models
    settings = config.get_settings()
    if 'es.host' in settings:
        app.config['ELASTICSEARCH_HOST'] = settings['es.host']
    if 'es.index' in settings:
        app.config['ELASTICSEARCH_INDEX'] = settings['es.index']
    es.init_app(app)
    with app.test_request_context():
        try:
            Annotation.create_all()
        except:
            Annotation.update_settings()
            Annotation.create_all()

    # Configure authentication and authorization
    app.config['AUTHZ_ON'] = True
    app.before_request(before_request)

    # Configure the API views -- version 1 is just an annotator.store proxy
    api_v1 = wsgiapp2(app)

    config.add_view(api_v1, route_name='api')

    # Add the store utility class to the registry
    config.set_request_property(Store, 'store', reify=True)
