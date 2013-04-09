__all__ = ['auth']

import urlparse

from annotator import auth
from pyramid.view import view_config


@view_config(renderer='string', request_method='GET', route_name='token')
def token(context, request):
    return context.token


def includeme(config):
    """Include the annotator-store API backend.

    Example INI file:

        [app:h]
        api.key: api.key: 00000000-0000-0000-0000-000000000000
        api.url: https://example.com/api/

    """

    api_url = config.registry.settings.get('api.url', '/api')

    if urlparse.urlparse(api_url).scheme:
        def set_app_url(request, elements, kw):
            kw.setdefault('_app_url', request.registry.settings['api.url'])
            return (elements, kw)
        config.add_route('api', '', pregenerator=set_app_url, static=True)
    else:
        pattern = '/'.join([api_url.strip('/'), '*subpath'])
        config.add_route('api', pattern)

    config.include('h.api.store')

    # And pick up the token view
    config.add_route('token', '/token')
    config.scan(__name__)
