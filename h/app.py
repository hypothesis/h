# -*- coding: utf-8 -*-
"""The main h application."""
import logging
import os

from pyramid.config import Configurator

from h.api.middleware import permit_cors
from h.config import settings_from_environment
from h.security import derive_key

log = logging.getLogger(__name__)


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

    app = config.make_wsgi_app()
    app = permit_cors(app,
                      allow_headers=(
                          'Authorization',
                          'Content-Type',
                          'X-Annotator-Auth-Token',
                          'X-Client-Id',
                      ),
                      allow_methods=('HEAD', 'GET', 'POST', 'PUT', 'DELETE'))

    return app


def includeme(config):

    config.include('h.features')

    config.include('h.db')
    config.include('h.models')
    config.include('h.views')
    config.include('h.renderers')
    config.include('h.api_client')

    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('.js')
    config.add_jinja2_renderer('.txt')
    config.add_jinja2_renderer('.html')
    config.add_jinja2_renderer('.xml')

    config.include('h.accounts')
    config.include('h.auth')
    config.include('h.claim')
    config.include('h.notification')
    config.include('h.queue')
    config.include('h.streamer')

    config.include('h.api', route_prefix='/api')

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

    return missing
