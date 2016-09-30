# -*- coding: utf-8 -*-

"""Configuration for the h application."""

from __future__ import unicode_literals

import logging
import os

from pyramid.config import Configurator
from pyramid.settings import asbool

from h.security import derive_key
from h.settings import DockerSetting
from h.settings import EnvSetting
from h.settings import SettingError
from h.settings import database_url
from h.settings import mandrill_settings

__all__ = ('configure',)

log = logging.getLogger(__name__)

# The list of all settings read from the system environment. These are in
# reverse-priority order, meaning that later settings trump earlier settings.
# In general, automatic setup (such as Docker links) is overridden by explicit
# settings.
SETTINGS = [
    # Automatic configuration of remote services via Docker links
    DockerSetting('es.host', 'elasticsearch',
                  pattern='http://{port_9200_tcp_addr}:{port_9200_tcp_port}'),
    DockerSetting('mail.host', 'mail',
                  pattern='{port_25_tcp_addr}'),
    DockerSetting('mail.port', 'mail', pattern='{port_25_tcp_port}'),
    DockerSetting('statsd.host', 'statsd', pattern='{port_8125_udp_addr}'),
    DockerSetting('statsd.port', 'statsd', pattern='{port_8125_udp_port}'),

    # Mailer configuration for Mandrill
    mandrill_settings,

    # Configuration for external components
    EnvSetting('broker_url', 'BROKER_URL'),
    EnvSetting('es.client_poolsize', 'ELASTICSEARCH_CLIENT_POOLSIZE',
               type=int),
    EnvSetting('es.client_timeout', 'ELASTICSEARCH_CLIENT_TIMEOUT', type=int),
    EnvSetting('es.host', 'ELASTICSEARCH_HOST'),
    EnvSetting('es.index', 'ELASTICSEARCH_INDEX'),
    EnvSetting('mail.default_sender', 'MAIL_DEFAULT_SENDER'),
    EnvSetting('mail.host', 'MAIL_HOST'),
    EnvSetting('mail.port', 'MAIL_PORT', type=int),
    EnvSetting('origins', 'ALLOWED_ORIGINS'),
    EnvSetting('sqlalchemy.url', 'DATABASE_URL', type=database_url),
    EnvSetting('statsd.host', 'STATSD_HOST'),
    EnvSetting('statsd.port', 'STATSD_PORT', type=int),

    # Configuration for Pyramid
    EnvSetting('secret_key', 'SECRET_KEY', type=bytes),

    # Configuration for h
    EnvSetting('csp.enabled', 'CSP_ENABLED', type=asbool),
    EnvSetting('csp.report_uri', 'CSP_REPORT_URI'),
    EnvSetting('csp.report_only', 'CSP_REPORT_ONLY'),
    EnvSetting('ga_tracking_id', 'GOOGLE_ANALYTICS_TRACKING_ID'),
    EnvSetting('h.app_url', 'APP_URL'),
    EnvSetting('h.auth_domain', 'AUTH_DOMAIN'),
    EnvSetting('h.bouncer_url', 'BOUNCER_URL'),
    EnvSetting('h.client_id', 'CLIENT_ID'),
    EnvSetting('h.client_secret', 'CLIENT_SECRET'),
    EnvSetting('h.db.should_create_all', 'MODEL_CREATE_ALL', type=asbool),
    EnvSetting('h.db.should_drop_all', 'MODEL_DROP_ALL', type=asbool),
    EnvSetting('h.proxy_auth', 'PROXY_AUTH', type=asbool),
    EnvSetting('h.search.autoconfig', 'SEARCH_AUTOCONFIG', type=asbool),
    EnvSetting('h.websocket_url', 'WEBSOCKET_URL'),
    # The client Sentry DSN should be of the public kind, lacking the password
    # component in the DSN URI.
    EnvSetting('h.client.sentry_dsn', 'SENTRY_DSN_CLIENT'),

    # Debug/development settings
    EnvSetting('debug_query', 'DEBUG_QUERY'),
]


def configure(environ=None, settings=None):
    if environ is None:
        environ = os.environ
    if settings is None:
        settings = {}

    for s in SETTINGS:
        try:
            result = s(environ)
        except SettingError as e:
            log.warn(e)

        if result is not None:
            settings.update(result)

    if 'secret_key' not in settings:
        log.warn('No secret key provided: using transient key. Please '
                 'configure the secret_key setting or the SECRET_KEY '
                 'environment variable!')
        settings['secret_key'] = os.urandom(64)

    # Set up SQLAlchemy debug logging
    if 'debug_query' in settings:
        level = logging.INFO
        if settings['debug_query'] == 'trace':
            level = logging.DEBUG
        logging.getLogger('sqlalchemy.engine').setLevel(level)

    return Configurator(settings=settings)
