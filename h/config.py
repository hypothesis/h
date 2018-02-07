# -*- coding: utf-8 -*-

"""Configuration for the h application."""

from __future__ import unicode_literals

import logging
import os

from pyramid.config import Configurator
from pyramid.settings import asbool, aslist

from h.settings import (
    DeprecatedSetting,
    EnvSetting,
    SettingError,
    database_url,
    mandrill_settings,
)
from h.util.logging_filters import ExceptionFilter

__all__ = ('configure',)

log = logging.getLogger(__name__)

# The default salt used for secret derivation. This is a public value, and can
# be overridden using the SECRET_SALT environment variable.
DEFAULT_SALT = (b"\xbc\x9ck!k\x81(\xb6I\xaa\x90\x0f'}\x07\xa1P\xd9\xb7\xcb"
                b"\xcb\xe8\x8b\t\xcf\xeb *\xa7\xa6\xe1i\xc7\x81\xe8\xd8\x18"
                b"\x9f\x1b\x96\xc1\xfa\x8b\x19\x82\xa3[\x19\xcb\xa4\x1a\x0f"
                b"\xe4\xcb\r\x17\x7f\xfbh\xd5^W\xdb\xe6")

# The list of all settings read from the system environment. These are in
# reverse-priority order, meaning that later settings trump earlier settings.
SETTINGS = [
    # Mailer configuration for Mandrill
    mandrill_settings,

    # Configuration for external components
    EnvSetting('broker_url', 'BROKER_URL'),
    EnvSetting('es.client_poolsize', 'ELASTICSEARCH_CLIENT_POOLSIZE',
               type=int),
    EnvSetting('es.client.max_retries', 'ELASTICSEARCH_CLIENT_MAX_RETRIES', type=int),
    EnvSetting('es.client.retry_on_timeout', 'ELASTICSEARCH_CLIENT_RETRY_ON_TIMEOUT', type=asbool),
    EnvSetting('es.client.timeout', 'ELASTICSEARCH_CLIENT_TIMEOUT', type=float),
    EnvSetting('es.host', 'ELASTICSEARCH_HOST'),
    EnvSetting('es.index', 'ELASTICSEARCH_INDEX'),
    EnvSetting('es.aws.access_key_id', 'ELASTICSEARCH_AWS_ACCESS_KEY_ID'),
    EnvSetting('es.aws.region', 'ELASTICSEARCH_AWS_REGION'),
    EnvSetting('es.aws.secret_access_key', 'ELASTICSEARCH_AWS_SECRET_ACCESS_KEY'),
    EnvSetting('mail.default_sender', 'MAIL_DEFAULT_SENDER'),
    EnvSetting('mail.host', 'MAIL_HOST'),
    EnvSetting('mail.port', 'MAIL_PORT', type=int),
    EnvSetting('sqlalchemy.url', 'DATABASE_URL', type=database_url),
    EnvSetting('statsd.host', 'STATSD_HOST'),
    EnvSetting('statsd.port', 'STATSD_PORT', type=int),
    EnvSetting('statsd.prefix', 'STATSD_PREFIX'),

    # Configuration for Pyramid
    EnvSetting('secret_key', 'SECRET_KEY', type=bytes),
    EnvSetting('secret_salt', 'SECRET_SALT', type=bytes),

    # Configuration for h
    EnvSetting('csp.enabled', 'CSP_ENABLED', type=asbool),
    EnvSetting('csp.report_uri', 'CSP_REPORT_URI'),
    EnvSetting('csp.report_only', 'CSP_REPORT_ONLY'),
    EnvSetting('ga_tracking_id', 'GOOGLE_ANALYTICS_TRACKING_ID'),
    EnvSetting('ga_client_tracking_id', 'GOOGLE_ANALYTICS_CLIENT_TRACKING_ID'),
    EnvSetting('h.app_url', 'APP_URL'),
    DeprecatedSetting(EnvSetting('h.authority', 'AUTH_DOMAIN'),
                      message='use the AUTHORITY environment variable instead'),
    EnvSetting('h.authority', 'AUTHORITY'),
    EnvSetting('h.bouncer_url', 'BOUNCER_URL'),

    EnvSetting('h.client_url', 'CLIENT_URL'),

    # ID for the OAuth authclient that the embedded client should use when
    # making requests to OAuth endpoints. As a public client, it does not have a
    # secret.
    EnvSetting('h.client_oauth_id', 'CLIENT_OAUTH_ID'),

    # The list of origins that the client will respond to cross-origin RPC
    # requests from.
    EnvSetting('h.client_rpc_allowed_origins',
               'CLIENT_RPC_ALLOWED_ORIGINS', type=aslist),

    EnvSetting('h.db_session_checks', 'DB_SESSION_CHECKS', type=asbool),

    # Environment name, provided by the deployment environment. Please do
    # *not* toggle functionality based on this value. It is intended as a
    # label only.
    EnvSetting('h.env', 'ENV'),
    # Where should logged-out users visiting the homepage be redirected?
    EnvSetting('h.homepage_redirect_url', 'HOMEPAGE_REDIRECT_URL'),
    EnvSetting('h.proxy_auth', 'PROXY_AUTH', type=asbool),
    # Sentry DSNs for frontend code should be of the public kind, lacking the
    # password component in the DSN URI.
    EnvSetting('h.sentry_dsn_client', 'SENTRY_DSN_CLIENT'),
    EnvSetting('h.sentry_dsn_frontend', 'SENTRY_DSN_FRONTEND'),
    EnvSetting('h.websocket_url', 'WEBSOCKET_URL'),

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

    # Use a fixed default salt if none provided
    if 'secret_salt' not in settings:
        settings['secret_salt'] = DEFAULT_SALT

    # Set up SQLAlchemy debug logging
    if 'debug_query' in settings:
        level = logging.INFO
        if settings['debug_query'] == 'trace':
            level = logging.DEBUG
        logging.getLogger('sqlalchemy.engine').setLevel(level)

    # Add ES logging filter to filter out ReadTimeout warnings
    es_logger = logging.getLogger('elasticsearch')
    es_logger.addFilter(ExceptionFilter((("ReadTimeout", "WARNING"),)))

    return Configurator(settings=settings)
