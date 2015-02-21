# -*- coding: utf-8 -*-
"""The main h application."""
from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.wsgi import wsgiapp2

from .auth import acl_authz, remote_authn, session_authn


def create_app(settings):
    """Configure and add static routes and views. Return the WSGI app."""
    config = Configurator(settings=settings)

    config.set_authentication_policy(session_authn)
    config.set_authorization_policy(acl_authz)
    config.set_root_factory('h.resources.RootFactory')

    config.add_subscriber('h.subscribers.add_renderer_globals',
                          'pyramid.events.BeforeRender')

    config.include('.')
    config.include('.features')

    if config.registry.feature('accounts'):
        config.include('.accounts')

    if config.registry.feature('api'):
        api_app = create_api(settings)
        api_view = wsgiapp2(api_app)
        config.add_view(api_view, name='api')

    if config.registry.feature('streamer'):
        config.include('.streamer')

    if config.registry.feature('notification'):
        config.include('.notification')

    return config.make_wsgi_app()


def create_api(settings):
    config = Configurator(settings=settings)

    config.set_authentication_policy(remote_authn)
    config.set_authorization_policy(acl_authz)
    config.set_root_factory('h.resources.APIResource')

    config.add_renderer('json', JSON(indent=4))
    config.add_subscriber('h.subscribers.set_user_from_oauth',
                          'pyramid.events.ContextFound')
    config.add_tween('h.tweens.annotator_tween_factory')

    config.include('.api')
    config.include('.auth')
    config.include('.features')

    if config.registry.feature('streamer'):
        config.include('.streamer')

    return config.make_wsgi_app()


def main(global_config, **settings):
    """Create the h application with all the awesomeness that is configured."""
    from h import config
    environ_config = config.settings_from_environment()
    settings.update(environ_config)  # from environment variables
    settings.update(global_config)   # from paste [DEFAULT] + command line
    return create_app(settings)
