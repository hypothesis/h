# -*- coding: utf-8 -*-
"""The main h application."""
import functools
import logging
import os

from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.wsgi import wsgiapp2

from h.api.middleware import permit_cors
from h.auth import acl_authz, remote_authn, session_authn
from h.config import settings_from_environment
from h.security import derive_key

log = logging.getLogger(__name__)


def strip_vhm(view):
    """A view decorator that strips the X-Vhm-Root header from the request.

    The X-Vhm-Root header is used by Pyramid for virtual hosting. The router
    treats the value of this header as a traversal prefix. When a view
    callable itself is an embedded Pyramid application, the inner application
    should not process this header again. In this situation, this decorator
    makes the virtual root work as intended.
    """
    @functools.wraps(view)
    def wrapped(context, request):
        request.headers.pop('X-Vhm-Root', None)
        return view(context, request)

    return wrapped


def create_app(global_config, **settings):
    """Configure and add static routes and views. Return the WSGI app."""
    settings = get_settings(global_config, **settings)

    config = Configurator(settings=settings)

    config.set_root_factory('h.resources.create_root')

    config.add_subscriber('h.subscribers.add_renderer_globals',
                          'pyramid.events.BeforeRender')

    config.include('h.features')

    config.include('h.db')
    config.include('h.views')
    config.include('h.renderers')
    config.include('h.api_client')

    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('.js')
    config.add_jinja2_renderer('.txt')
    config.add_jinja2_renderer('.html')
    config.add_jinja2_renderer('.xml')

    config.add_tween('h.tweens.csrf_tween_factory')

    if config.registry.feature('accounts'):
        config.set_authentication_policy(session_authn)
        config.set_authorization_policy(acl_authz)
        config.include('h.accounts')

    if config.registry.feature('api'):
        api_app = create_api(settings)
        api_view = wsgiapp2(api_app)
        config.add_view(api_view, name='api', decorator=strip_vhm)
        # Add the view again with the 'index' route name, otherwise it will
        # not take precedence over the index when a virtual root is in use.
        config.add_view(api_view, name='api', decorator=strip_vhm,
                        route_name='index')

    if config.registry.feature('claim'):
        config.include('h.claim')

    if config.registry.feature('queue'):
        config.include('h.queue')

    if config.registry.feature('streamer'):
        config.include('h.streamer')

    if config.registry.feature('notification'):
        config.include('h.notification')

    return config.make_wsgi_app()


def create_api(global_config, **settings):
    settings = get_settings(global_config, **settings)

    config = Configurator(settings=settings)

    config.set_authentication_policy(remote_authn)
    config.set_authorization_policy(acl_authz)
    config.set_root_factory('h.api.resources.create_root')

    config.add_renderer('json', JSON(indent=4))
    config.add_subscriber('h.api.subscribers.set_user_from_oauth',
                          'pyramid.events.ContextFound')
    config.add_tween('h.api.tweens.auth_token')

    config.include('h.features')

    config.include('h.auth')
    config.include('h.api.db')
    config.include('h.api.views')

    if config.registry.feature('queue'):
        config.include('h.queue')
        config.include('h.api.queue')

    app = config.make_wsgi_app()
    app = permit_cors(app,
                      allow_headers=('Authorization',
                                     'X-Annotator-Auth-Token'),
                      allow_methods=('HEAD', 'GET', 'POST', 'PUT', 'DELETE'))

    return app


def get_settings(global_config, **settings):
    """
    Return a paste settings objects extended as necessary with data from the
    environment.
    """
    result = {}
    result.update(settings)
    result.update(settings_from_environment())
    result.update(global_config)
    result.update(missing_secrets(result))
    return result


def missing_secrets(settings):
    missing = {}

    if 'secret_key' not in settings:
        log.warn('No secret key provided: using transient key. Please '
                 'configure the secret_key setting or the SECRET_KEY '
                 'environment variable!')
        missing['secret_key'] = os.urandom(64)

    # If the redis session secret hasn't been set explicitly, derive it from
    # the global secret key.
    if 'redis.sessions.secret' not in settings:
        secret = settings.get('secret_key')
        if secret is None:
            secret = missing['secret_key']
        missing['redis.sessions.secret'] = derive_key(secret, 'h.session')

    return missing
