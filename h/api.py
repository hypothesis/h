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
    hypothesis_key = settings.get('h.consumer_key')
    if key == hypothesis_key:
        consumer = Consumer(key=hypothesis_key)
        consumer.secret = settings.get('h.api_secret')
        consumer.ttl = settings.get('h.api_ttl', auth.DEFAULT_TTL)
        return consumer
    else:
        return request.db.query(Consumer).get(key)

def token_headers(request):
    headers = {
        'Access-Control-Allow-Origin': request.headers.get('origin'),
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Expose-Headers': 'Location, Content-Type, Content-Length'
    }
    if request.method == 'OPTIONS': headers.update({
        'Access-Control-Allow-Headers': 'Content-Type, Content-Length, X-Requested-With',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Max-Age': '86400'
    })
    return headers

def token(request):
    settings = request.registry.settings
    secret = settings.get('h.api_secret')
    key = settings.get('h.consumer_key')
    ttl = settings.get('h.api_ttl', auth.DEFAULT_TTL)
    # @@ make this deal with oid+realms, oauth etc better
    user_id = 'acct:%s@%s' % (request.user.users[0].login, request.host)
    message = {
        'userId': user_id,
        'consumerKey': key,
        'ttl': ttl
    }
    body = auth.encode_token(message, secret)
    return Response(body=body, headerlist=token_headers(request).items())

def users(request):
    return map(
        lambda user: (user.id, (user.login if user.provider == 'local'
                                else '%s@%s' % (user.login, user.provider))),
        request.user and request.user.users or [])

def includeme(config):
    settings = config.registry.settings

    if not settings.has_key('h.consumer_key'):
        raise KeyError('h.consumer_key')

    if not settings.has_key('h.consumer_secret'):
        raise KeyError('h.consumer_secret')

    # Create the annotator-store app
    app = Flask(__name__)
    app.register_blueprint(store.store)

    # Set up the models
    es.init_app(app)
    with app.test_request_context():
        try:
            Annotation.create_all()
        except:
            Annotation.update_settings()
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
    config.add_view(users, route_name='users', request_method='GET',
                    permission='authenticated',
                    renderer='json')
    config.add_view(lambda r: Response(headerlist=token_headers(r).items()),
                    route_name='token', request_method='OPTIONS')
