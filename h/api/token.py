import urlparse

from annotator import auth
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.security import authenticated_userid
from pyramid.view import view_config, view_defaults

from h import interfaces, views


@view_defaults(renderer='string', route_name='token')
class TokenController(views.BaseController):
    @view_config(request_method="GET")
    def __call__(self):
        request = self.request

        consumer = self.Consumer.get_by_key(self.settings['api.key'])
        assert(consumer)

        message = {
            'consumerKey': str(consumer.key),
            'ttl': consumer.ttl,
        }

        userid = authenticated_userid(request)

        if isinstance(userid, basestring):
            message['userId'] = userid
        elif request.user:
            message['userId'] = "acct:%(username)s@%(provider)s" % {
                'username': request.user.username,
                'provider': request.server_name
            }

        return auth.encode_token(message, consumer.secret)

    @classmethod
    def __json__(cls, request):
        return cls(request)()


class AuthTokenAuthenticationPolicy(CallbackAuthenticationPolicy):
    def callback(self, userid, request):
        Consumer = request.registry.queryUtility(interfaces.IConsumerClass)
        user = auth.Authenticator(Consumer.get_by_key).request_user(request)
        if user:
            return [user.id]
        return None

    def unauthenticated_userid(self, request):
        token = request.headers.get('X-Annotator-Auth-Token')
        try:
            unsafe = auth.decode_token(token, verify=False)
        except auth.TokenInvalid:
            return None
        else:
            return unsafe.get('userId')

    def remember(self, request, principal, *kw):
        return []

    def forget(self, request):
        return []


def includeme(config):
    """Include an auth token generator.

    Example INI file:

    .. code-block:: ini
        [app:h]
        api.token_endpoint: /api/token
    """

    token_endpoint = config.registry.settings.get(
        'api.token_endpoint',
        '/api/token'
    ).strip('/')
    config.add_route('token', token_endpoint)
    config.scan(__name__)

    if not config.registry.queryUtility(interfaces.ITokenClass):
        config.registry.registerUtility(
            TokenController,
            interfaces.ITokenClass
        )

    config.set_authentication_policy(AuthTokenAuthenticationPolicy())
