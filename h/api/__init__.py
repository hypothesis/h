__all__ = ['auth']

import urlparse

from annotator import auth
from pyramid.view import view_config

from h import views
from h import streamer

import logging
log = logging.getLogger(__name__)


@view_config(renderer='string', request_method='GET', route_name='token')
class TokenController(views.BaseController):
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


def includeme(config):
    """Include the annotator-store API backend.

    Example INI file:

        [app:h]
        api.key: api.key: 00000000-0000-0000-0000-000000000000
        api.url: https://example.com/api

    """

    settings = config.get_settings()

    #configure streamer
    if 'streamer.port' in settings:
        streamer.init_streamer(settings['streamer.port'], settings['ssl_pem'])

    api_url = config.registry.settings.get('api.url', '/api')

    if urlparse.urlparse(api_url).scheme:
        def set_app_url(request, elements, kw):
            kw.setdefault('_app_url', request.registry.settings['api.url'])
            return (elements, kw)
        config.add_route('api', '', pregenerator=set_app_url, static=True)
    else:
        api_path = api_url.strip('/')
        api_pattern = '/'.join([api_path, '*subpath'])
        token_pattern = '/'.join([api_path, 'token'])
        config.add_route('token', token_pattern)
        config.add_route('api', api_pattern)
        config.include('h.api.store')
        config.scan(__name__)
