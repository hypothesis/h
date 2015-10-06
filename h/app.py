# -*- coding: utf-8 -*-
"""The main h application."""
import logging
import os

from pyramid.config import Configurator

from h.config import settings_from_environment
from h.security import derive_key

log = logging.getLogger(__name__)


def configure_jinja2_assets(config):
    assets_env = config.get_webassets_env()
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.assets_environment = assets_env


def create_app(global_config, **settings):
    """Configure and add static routes and views. Return the WSGI app."""
    settings = get_settings(global_config, **settings)

    config = Configurator(settings=settings)

    config.set_root_factory('h.resources.create_root')

    config.add_subscriber('h.subscribers.add_renderer_globals',
                          'pyramid.events.BeforeRender')
    config.add_subscriber('h.subscribers.set_user_from_oauth',
                          'pyramid.events.NewRequest')

    config.add_tween('h.tweens.csrf_tween_factory')
    config.add_tween('h.tweens.auth_token')

    config.include(__name__)

    return config.make_wsgi_app()


def includeme(config):

    config.include('h.features')

    config.include('h.db')
    config.include('h.form')
    config.include('h.hashids')
    config.include('h.models')
    config.include('h.views')
    config.include('h.feeds')

    config.include('pyramid_jinja2')
    config.add_jinja2_extension('h.jinja_extensions.IncludeRawExtension')
    config.add_jinja2_extension('webassets.ext.jinja2.AssetsExtension')
    # Register a deferred action to bind the webassets environment to the
    # Jinja2 webassets extension when the configuration is committed.
    config.action(None, configure_jinja2_assets, args=(config,))

    config.include('h.accounts')
    config.include('h.admin')
    config.include('h.auth')
    config.include('h.claim')
    config.include('h.groups')
    config.include('h.notification')
    config.include('h.queue')
    config.include('h.streamer')

    config.include('h.api', route_prefix='/api')
    config.include('h.api.nipsa')
    config.include('h.db')

    # Override the traversal path for the api index route.
    config.add_route('api', '/api/', traverse='/api/')

    # Support virtual hosting the API over the index route with X-Vhm-Root.
    config.add_view('h.api.views.index',
                    context='h.api.resources.Root',
                    renderer='json',
                    route_name='index')


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

    if 'h.hashids.salt' not in settings:
        log.warn('No salt provided for hashids: using transient value. This '
                 'will result in URLs that are unstable across application '
                 'restarts! Configure the h.hashids.salt setting or the '
                 'HASHIDS_SALT environment variable!')
        missing['h.hashids.salt'] = os.urandom(64)

    return missing
