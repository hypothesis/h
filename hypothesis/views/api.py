from flask import Flask, g

from pyramid.exceptions import Forbidden
from pyramid.response import Response
from pyramid.security import Authenticated
from pyramid.threadlocal import get_current_request
from pyramid.view import view_config, view_defaults
from pyramid.wsgi import wsgiapp2

from annotator import auth, authz, store, es

from .. models.api import Consumer

def consumer_fetcher(key):
    request = get_current_request()
    settings = request.registry.settings
    hypothesis_key = settings.get('hypothesis.consumer_key')
    if key == hypothesis_key:
        consumer = Consumer(key=hypothesis_key)
        consumer.secret = settings.get('hypothesis.api_secret')
        consumer.ttl = settings.get('hypothesis.api_ttl', auth.DEFAULT_TTL)
        return consumer
    else:
        return request.db.query(Consumer).get(key)

def cors_headers(request):
    return {
        'Access-Control-Allow-Origin': request.headers.get('origin', '*'),
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Expose-Headers': 'Location, Content-Type, Content-Length'
    }

@view_config(route_name='token', request_method='GET',
             permission='authenticated')
def token_get(request):
    settings = request.registry.settings
    secret = settings.get('hypothesis.api_secret')
    key = settings.get('hypothesis.consumer_key')
    ttl = settings.get('hypothesis.api_ttl', auth.DEFAULT_TTL)
    user_id = request.user.id
    message = {
        'userId': user_id,
        'consumerKey': key,
        'ttl': ttl
    }
    body = auth.encode_token(message, secret)
    return Response(body=body, headerlist=cors_headers(request).items())

@view_config(route_name='token', request_method='OPTIONS')
def token_options(request):
    headers = cors_headers(request)
    headers.update({
        'Access-Control-Allow-Headers': 'X-Requested-With, Content-Type, Content-Length',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Max-Age': '86400'
    })
    return Response(headerlist=headers.items())

def includeme(config):
    # Create the annotator-store flask app and configure it
    app = Flask('annotator')
    # Set up the elastic-search configuration
    es.init_app(app)
    # Set up the store blueprint
    app.register_blueprint(store.store)

    # Wrapper function to set up authorization hooks for the store
    def before_request():
        g.auth = auth.Authenticator(consumer_fetcher)
        g.authorize = authz.authorize
    app.before_request(before_request)

    # Set up a view to delegate API calls
    config.add_view(wsgiapp2(app), route_name='store')
