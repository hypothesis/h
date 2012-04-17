from annotator import auth, authz, store, es
from annotator.annotation import Annotation

from flask import Flask, g

from pyramid.response import Response
from pyramid.threadlocal import get_current_request
from pyramid.wsgi import wsgiapp2

from . models import Consumer

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
    headers = {
        'Access-Control-Allow-Origin': request.headers.get('origin', '*'),
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Expose-Headers': 'Location, Content-Type, Content-Length'
    }
    if request.method == 'OPTIONS': headers.update({
        'Access-Control-Allow-Headers': 'X-Requested-With, Content-Type, Content-Length',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Max-Age': '86400'
    })
    return headers

def token(request):
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

def includeme(config):
    settings = config.registry.settings

    if not settings.has_key('hypothesis.consumer_key'):
        raise KeyError('hypothesis.consumer_key')

    if not settings.has_key('hypothesis.consumer_secret'):
        raise KeyError('hypothesis.consumer_secret')

    # Create the annotator-store app
    app = Flask(__name__)
    app.register_blueprint(store.store)

    # Set up the models
    es.init_app(app)
    with app.test_request_context():
        Annotation.create_all()

    # Configure authentication (ours) and authorization (store)
    authenticator = auth.Authenticator(consumer_fetcher)
    def before_request():
        g.auth = authenticator
        g.authorize = authz.authorize
    app.before_request(before_request)

    # Configure the API views
    config.add_view(wsgiapp2(app), route_name='api')
    config.add_view(token, route_name='token', request_method='GET',
                    permission='authenticated')
    config.add_view(lambda r: Response(headerlist=cors_headers(r).items()),
                    route_name='token', request_method='OPTIONS')
