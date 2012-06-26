from annotator import auth, authz, store, es
from annotator.annotation import Annotation

from flask import Flask, g

from pyramid.response import Response
from pyramid.threadlocal import get_current_request
from pyramid.wsgi import wsgiapp2

from . models import Consumer

def consumer_fetcher(key):
    """Look an api consumer up by key.

    The annotator-store `annotator.Authenticator` uses this function in the
    process of authenticating requests to verify the secrets of the JSON Web
    Token passed by the consumer client.

    """

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

def token(request):
    """Get an API token for the logged in user."""

    # Cross-Origin Resource Sharing headers needed for the token request
    # include credentials so that the user can be authenticated.
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

    # The response is a JSON Web Token signed with the application's consumer
    # key and secret. In the future, other applications may have their own
    # consumer keys. Although, most of this should go away in favor of more
    # traditional OAuth tools and the need for the token request might be
    # made to vanish when the iframe architecture settles and cross-domain
    # communication is handled at the browser runtime via postMessage.
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
    return Response(body=body, headerlist=headers.items())

def users(request):
    """Retrieve all the profiles assocatied with a principal."""
    return map(
        lambda user: (user.id, (user.login if user.provider == 'local'
                                else '%s@%s' % (user.login, user.provider))),
        request.user and request.user.users or [])

def includeme(config):
    """Include the annotator-store API backend.

    Example INI file:

        [app:h]
        consumer_key: primary_consumer
        consumer_secret: 00000000-0000-0000-0000-000000000000

    """

    settings = config.get_settings()

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
    config.add_view(token, route_name='token', permission='authenticated')
    config.add_view(users, route_name='users', request_method='GET',
                    permission='authenticated',
                    renderer='json')
