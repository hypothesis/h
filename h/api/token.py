# -*- coding: utf-8 -*-
from annotator import auth
from pyramid.authentication import RemoteUserAuthenticationPolicy
from pyramid.view import view_config

from h.api import lib


@view_config(renderer='string', route_name='token')
def token(request):
    key = request.registry.settings['api.key']
    consumer = lib.get_consumer(request, key)
    assert(consumer)

    persona = request.params.get('persona')
    personas = request.session.get('personas', [])

    message = {
        'consumerKey': str(consumer.key),
        'ttl': consumer.ttl,
    }

    try:
        message['userId'] = next(p for p in personas if p == persona)
    except StopIteration:
        pass

    return auth.encode_token(message, consumer.secret)


class AuthTokenAuthenticationPolicy(RemoteUserAuthenticationPolicy):
    def unauthenticated_userid(self, request):
        auth_token = request.environ.get(self.environ_key)
        try:
            unsafe = auth.decode_token(auth_token, verify=False) or {}
            return unsafe.get('userId')
        except auth.TokenInvalid:
            return None


def groupfinder(userid, request):
    user = lib.authenticator(request).request_user(request)
    if user:
        # TODO: Group support for auth tokens
        return []
    return None


def includeme(config):
    """Include an auth token generator.

    Example INI file:

    .. code-block:: ini
        [app:h]
        api.token_endpoint: /api/token
    """
    registry = config.registry
    settings = registry.settings

    authn_debug = settings.get('pyramid.debug_authorization') \
        or settings.get('debug_authorization')
    authn_policy = AuthTokenAuthenticationPolicy(
        environ_key='HTTP_X_ANNOTATOR_AUTH_TOKEN',
        callback=groupfinder,
        debug=authn_debug,
    )
    config.set_authentication_policy(authn_policy)

    token_url = settings.get('api.token_endpoint', '/api/token').strip('/')
    config.add_route('token', token_url)
    config.scan(__name__)
