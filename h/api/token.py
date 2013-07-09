import urlparse

from annotator import auth
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

        if request.user:
            parts = {
                'username': request.user.username,
                'provider': request.host
            }
            message['userId'] = 'acct:%(username)s@%(provider)s' % parts

        return auth.encode_token(message, consumer.secret)

    @classmethod
    def __json__(cls, request):
        return cls(request)()


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
