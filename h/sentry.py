# -*- coding: utf-8 -*-
"""
Provide a Sentry client at `request.sentry`.

This module provides a Sentry client, preconfigured with appropriate request
context, as a request property, `request.sentry`. This allows us to more easily
log exceptions from within the application with a useful complement of
diagnostic data.
"""

import logging
from os import getenv

import raven
from raven.transport import GeventedHTTPTransport
from raven.utils.wsgi import get_environ

log = logging.getLogger(__name__)


class SentryStub(object):

    """A stub for raven.Client in environments without a Sentry DSN."""

    warning_emitted = False

    def __new__(cls, *args, **kwargs):
        instance = super(SentryStub, cls).__new__(cls, *args, **kwargs)
        if not cls.warning_emitted:
            cls.warning_emitted = True
            log.warning('SENTRY_DSN not set, errors will not be reported')
        return instance

    def get_public_dsn(self, *args, **kwargs):
        return None

    def captureException(self, *args, **kwargs):
        pass

    def captureMessage(self, message, **kwargs):
        log.warning(message)
        pass


def http_context_data(request):
    return {
        'url': request.url,
        'method': request.method,
        'data': request.body,
        'query_string': request.query_string,
        'cookies': dict(request.cookies),
        'headers': dict(request.headers),
        'env': dict(get_environ(request.environ)),
    }


def user_context_data(request):
    return {
        'id': request.authenticated_userid,
        'ip_address': request.client_addr,
    }


def get_client(request):
    """
    Get a Sentry client configured with context data for the current request.
    """

    # If the `raven.transport` setting is set to 'gevent', then we use the
    # raven-supplied gevent compatible transport.
    transport_name = request.registry.settings.get('raven.transport')
    transport = GeventedHTTPTransport if transport_name == 'gevent' else None

    if not getenv('SENTRY_DSN'):
        return SentryStub()

    client = raven.Client(release=raven.fetch_package_version('h'),
                          transport=transport)
    client.http_context(http_context_data(request))
    client.user_context(user_context_data(request))
    return client


def includeme(config):
    config.add_request_method(get_client, 'sentry', reify=True)
