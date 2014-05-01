# -*- coding: utf-8 -*-
from annotator import auth
from pyramid.authentication import RemoteUserAuthenticationPolicy
from pyramid.view import view_config, view_defaults

from h import interfaces, views


@view_defaults(renderer='string', route_name='token')
class TokenController(views.BaseController):
    # pylint: disable=too-few-public-methods

    @view_config(request_method="GET")
    def __call__(self):
        request = self.request

        consumer = self.Consumer.get_by_key(request, self.settings['api.key'])
        assert(consumer)

        persona = request.params.get('persona')
        message = {
            'consumerKey': str(consumer.key),
            'ttl': consumer.ttl,
        }

        try:
            message['userId'] = next(
                principal
                for principal in request.effective_principals
                if principal == persona
                or (persona is None and principal.startswith('acct:'))
            )
        except StopIteration:
            pass

        return auth.encode_token(message, consumer.secret)

    @classmethod
    def __json__(cls, request):
        return cls(request)()


class AuthTokenAuthenticationPolicy(RemoteUserAuthenticationPolicy):
    def unauthenticated_userid(self, request):
        token = request.environ.get(self.environ_key)
        try:
            unsafe = auth.decode_token(token, verify=False) or {}
            return unsafe.get('userId')
        except auth.TokenInvalid:
            return None


def groupfinder(userid, request):
    Consumer = request.registry.queryUtility(interfaces.IConsumerClass)
    user = auth.Authenticator(Consumer.get_by_key).request_user(request)
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

    if not registry.queryUtility(interfaces.ITokenClass):
        registry.registerUtility(
            TokenController,
            interfaces.ITokenClass
        )

    token_url = settings.get('api.token_endpoint', '/api/token').strip('/')
    config.add_route('token', token_url)
    config.scan(__name__)
