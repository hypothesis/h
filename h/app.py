# -*- coding: utf-8 -*-

"""The main h application."""

from __future__ import unicode_literals

import collections
import logging

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.settings import asbool
from pyramid.tweens import EXCVIEW
import zope.sqlalchemy

from h import assets
from h import db
from h.auth.policy import AuthenticationPolicy
from h.config import configure

log = logging.getLogger(__name__)


def configure_jinja2_assets(config):
    assets_env = assets.Environment('/assets',
                                    'h/assets.ini',
                                    'build/manifest.json')
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.globals['asset_urls'] = assets_env.urls


def in_debug_mode(request):
    return asbool(request.registry.settings.get('pyramid.debug_all'))


def tm_activate_hook(request):
    if request.path.startswith(('/assets/', '/_debug_toolbar/')):
        return False
    return True


def create_app(global_config, **settings):
    """
    Create the h WSGI application.

    This function serves as a paste app factory.
    """
    config = configure(settings=settings)
    config.include(__name__)
    return config.make_wsgi_app()


def includeme(config):
    config.set_root_factory('h.resources:Root')

    config.add_subscriber('h.subscribers.add_renderer_globals',
                          'pyramid.events.BeforeRender')
    config.add_subscriber('h.subscribers.publish_annotation_event',
                          'h.api.events.AnnotationEvent')
    config.add_subscriber('h.subscribers.send_reply_notifications',
                          'h.api.events.AnnotationEvent')

    config.add_tween('h.tweens.conditional_http_tween_factory', under=EXCVIEW)
    config.add_tween('h.tweens.csrf_tween_factory')
    config.add_tween('h.tweens.auth_token')
    config.add_tween('h.tweens.content_security_policy_tween_factory')

    config.add_renderer('csv', 'h.renderers.CSV')
    config.add_request_method(in_debug_mode, 'debug', reify=True)

    config.include('pyramid_jinja2')
    config.add_jinja2_extension('h.jinja_extensions.Filters')
    # Register a deferred action to setup the assets environment
    # when the configuration is committed.
    config.action(None, configure_jinja2_assets, args=(config,))

    # Pyramid service layer: provides infrastructure for registering and
    # retrieving services bound to the request.
    config.include('pyramid_services')

    # Configure the transaction manager to support retrying retryable
    # exceptions. We also register the session factory with the thread-local
    # transaction manager, so that all sessions it creates are registered.
    config.add_settings({
        "tm.attempts": 3,
        "tm.activate_hook": tm_activate_hook,
        "tm.annotate_user": False,
    })
    config.include('pyramid_tm')
    zope.sqlalchemy.register(db.Session)

    # Enable a Content Security Policy
    # This is initially copied from:
    # https://github.com/pypa/warehouse/blob/e1cf03faf9bbaa15d67d0de2c70f9a9f732596aa/warehouse/config.py#L327
    config.add_settings({
        "csp": {
            "font-src": ["'self'", "fonts.gstatic.com"],
            "report-uri": [config.registry.settings.get("csp.report_uri")],
            "script-src": ["'self'"],
            "style-src": ["'self'", "fonts.googleapis.com"],
        },
    })

    # Set up pyramid authentication and authorization policies. See the Pyramid
    # documentation at:
    #
    #   http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/security.html
    #
    config.set_authentication_policy(AuthenticationPolicy())
    config.set_authorization_policy(ACLAuthorizationPolicy())

    # API module
    #
    # We include this first so that:
    # - configuration directives provided by modules in `h.api` are available
    #   to the rest of the application at startup.
    # - we can override behaviour from `h.api` if necessary.
    config.include('h.api', route_prefix='/api')

    # Core site modules
    config.include('h.assets')
    config.include('h.auth')
    config.include('h.db')
    config.include('h.features')
    config.include('h.form')
    config.include('h.indexer')
    config.include('h.models')
    config.include('h.realtime')
    config.include('h.sentry')
    config.include('h.stats')
    config.include('h.views')

    # Site modules
    config.include('h.accounts')
    config.include('h.admin', route_prefix='/admin')
    config.include('h.badge')
    config.include('h.feeds')
    config.include('h.groups')
    config.include('h.links')
    config.include('h.nipsa')
    config.include('h.notification')
