# -*- coding: utf-8 -*-

"""Configuration for the h application."""

from __future__ import unicode_literals

import logging
import os

from pyramid.config import Configurator
from pyramid.settings import asbool, aslist

from h.settings import database_url, SettingsManager
from h.util.logging_filters import ExceptionFilter

__all__ = ("configure",)

log = logging.getLogger(__name__)

# The default salt used for secret derivation. This is a public value, and can
# be overridden using the SECRET_SALT environment variable.
DEFAULT_SALT = (
    b"\xbc\x9ck!k\x81(\xb6I\xaa\x90\x0f'}\x07\xa1P\xd9\xb7\xcb"
    b"\xcb\xe8\x8b\t\xcf\xeb *\xa7\xa6\xe1i\xc7\x81\xe8\xd8\x18"
    b"\x9f\x1b\x96\xc1\xfa\x8b\x19\x82\xa3[\x19\xcb\xa4\x1a\x0f"
    b"\xe4\xcb\r\x17\x7f\xfbh\xd5^W\xdb\xe6"
)


def configure(environ=None, settings=None):
    if environ is None:
        environ = os.environ
    if settings is None:
        settings = {}
    settings_manager = SettingsManager(settings, environ)
    # Configuration for external components
    settings_manager.set("broker_url", "BROKER_URL")
    settings_manager.set(
        "es.client_poolsize", "ELASTICSEARCH_CLIENT_POOLSIZE", type_=int
    )
    settings_manager.set(
        "es.client.max_retries", "ELASTICSEARCH_CLIENT_MAX_RETRIES", type_=int
    )
    settings_manager.set(
        "es.client.retry_on_timeout",
        "ELASTICSEARCH_CLIENT_RETRY_ON_TIMEOUT",
        type_=asbool,
    )
    settings_manager.set(
        "es.client.timeout", "ELASTICSEARCH_CLIENT_TIMEOUT", type_=float
    )
    settings_manager.set("es.url", "ELASTICSEARCH_URL", required=True),
    settings_manager.set("es.index", "ELASTICSEARCH_INDEX")
    settings_manager.set(
        "es.check_icu_plugin",
        "ELASTICSEARCH_CHECK_ICU_PLUGIN",
        type_=asbool,
        default=True,
    )
    settings_manager.set("mail.default_sender", "MAIL_DEFAULT_SENDER")
    settings_manager.set("mail.host", "MAIL_HOST")
    settings_manager.set("mail.port", "MAIL_PORT", type_=int)
    settings_manager.set(
        "sqlalchemy.url", "DATABASE_URL", type_=database_url, required=True
    )
    settings_manager.set("statsd.host", "STATSD_HOST")
    settings_manager.set("statsd.port", "STATSD_PORT", type_=int)
    settings_manager.set("statsd.prefix", "STATSD_PREFIX")

    # Configuration for Pyramid
    settings_manager.set("secret_key", "SECRET_KEY", type_=_to_utf8, required=True)
    settings_manager.set(
        "secret_salt", "SECRET_SALT", type_=_to_utf8, default=DEFAULT_SALT
    )

    # Configuration for h
    settings_manager.set("csp.enabled", "CSP_ENABLED", type_=asbool)
    settings_manager.set("csp.report_uri", "CSP_REPORT_URI")
    settings_manager.set("csp.report_only", "CSP_REPORT_ONLY")
    settings_manager.set("ga_tracking_id", "GOOGLE_ANALYTICS_TRACKING_ID")
    settings_manager.set("ga_client_tracking_id", "GOOGLE_ANALYTICS_CLIENT_TRACKING_ID")
    settings_manager.set("h.app_url", "APP_URL")
    settings_manager.set(
        "h.authority",
        "AUTH_DOMAIN",
        deprecated_msg="use the AUTHORITY environment variable instead",
    )
    settings_manager.set("h.authority", "AUTHORITY")
    settings_manager.set("h.bouncer_url", "BOUNCER_URL")

    settings_manager.set("h.client_url", "CLIENT_URL")

    # ID for the OAuth authclient that the embedded client should use when
    # making requests to OAuth endpoints. As a public client, it does not have a
    # secret.
    settings_manager.set("h.client_oauth_id", "CLIENT_OAUTH_ID")

    # The list of origins that the client will respond to cross-origin RPC
    # requests from.
    settings_manager.set(
        "h.client_rpc_allowed_origins", "CLIENT_RPC_ALLOWED_ORIGINS", type_=aslist
    )

    settings_manager.set("h.db_session_checks", "DB_SESSION_CHECKS", type_=asbool)

    # Environment name, provided by the deployment environment. Please do
    # *not* toggle functionality based on this value. It is intended as a
    # label only.
    settings_manager.set("h.env", "ENV")
    # Where should logged-out users visiting the homepage be redirected?
    settings_manager.set("h.homepage_redirect_url", "HOMEPAGE_REDIRECT_URL")
    settings_manager.set("h.proxy_auth", "PROXY_AUTH", type_=asbool)
    # Sentry DSNs for frontend code should be of the public kind, lacking the
    # password component in the DSN URI.
    settings_manager.set("h.sentry_dsn_client", "SENTRY_DSN_CLIENT")
    settings_manager.set("h.sentry_dsn_frontend", "SENTRY_DSN_FRONTEND")
    settings_manager.set("h.sentry_environment", "SENTRY_ENVIRONMENT", default="dev")
    settings_manager.set("h.websocket_url", "WEBSOCKET_URL")

    # Debug/development settings
    settings_manager.set("debug_query", "DEBUG_QUERY")

    if "MANDRILL_USERNAME" in environ and "MANDRILL_APIKEY" in environ:
        settings_manager.set("mail.username", "MANDRILL_USERNAME")
        settings_manager.set("mail.password", "MANDRILL_APIKEY")
        settings_manager.set(
            "mail.host", "MANDRILL_HOST", default="smtp.mandrillapp.com"
        )
        settings_manager.set("mail.port", "MANDRILL_PORT", default=587)
        settings_manager.set("mail.tls", "MANDRILL_TLS", default=True)

    # Get resolved settings.
    settings = settings_manager.settings

    # Set up SQLAlchemy debug logging
    if "debug_query" in settings:
        level = logging.INFO
        if settings["debug_query"] == "trace":
            level = logging.DEBUG
        logging.getLogger("sqlalchemy.engine").setLevel(level)

    # Add ES logging filter to filter out ReadTimeout warnings
    es_logger = logging.getLogger("elasticsearch")
    es_logger.addFilter(ExceptionFilter((("ReadTimeoutError", "WARNING"),)))

    return Configurator(settings=settings)


def _to_utf8(str_or_bytes):
    if isinstance(str_or_bytes, bytes):
        return str_or_bytes
    return str_or_bytes.encode("utf-8")
