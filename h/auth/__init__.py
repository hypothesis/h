# -*- coding: utf-8 -*-

"""
Configure authentication for the application.

Configure and apply the appropriate authentication policy based on
app settings, and set some authentication- and authority-related
methods on the ``request``.

This module also provides some defined roles (reusable principals) and functionality
for generating user tokens.

The possible authentication policies for the application include:

DEFAULT POLICY: The default authentication policy uses an API policy for
                requests to API services, and a ticket policy for other requests.
PROXY POLICY:   If the app is configured for proxy authentication, the
                authentication policy will still use an API policy for API requests,
                but will use a proxy-specific authentication policy for other
                requests.
WEBSOCKET POLICY: Used for websocket requests. See :mod:`h.websocket`
"""
from __future__ import unicode_literals

import logging

from pyramid.authentication import RemoteUserAuthenticationPolicy
import pyramid_authsanity

from h.auth.policy import AuthenticationPolicy
from h.auth.policy import APIAuthenticationPolicy
from h.auth.policy import AuthClientPolicy
from h.auth.policy import TokenAuthenticationPolicy
from h.auth.util import default_authority, groupfinder
from h.security import derive_key

__all__ = (
    'DEFAULT_POLICY',
    'WEBSOCKET_POLICY',
)

log = logging.getLogger(__name__)

# Configure policy for authentication against API services.
# The API policy makes use of two "sub-policies",
# Token and AuthClient. The API policy in turn is used by the
# app-wide policy.
TOKEN_POLICY = TokenAuthenticationPolicy(callback=groupfinder)
AUTH_CLIENT_POLICY = AuthClientPolicy()
API_POLICY = APIAuthenticationPolicy(user_policy=TOKEN_POLICY,
                                     client_policy=AUTH_CLIENT_POLICY)


# The default policy for the entire app combines the API policy
# (for API requests) with a ticket policy (for other requests)
TICKET_POLICY = pyramid_authsanity.AuthServicePolicy()
DEFAULT_POLICY = AuthenticationPolicy(api_policy=API_POLICY,
                                      fallback_policy=TICKET_POLICY)


# If proxy auth is enabled, PROXY_POLICY is used instead of DEFAULT_POLICY
PROXY_FALLBACK_POLICY = RemoteUserAuthenticationPolicy(environ_key='HTTP_X_FORWARDED_USER',
                                                       callback=groupfinder)
PROXY_POLICY = AuthenticationPolicy(api_policy=API_POLICY,
                                    fallback_policy=PROXY_FALLBACK_POLICY)

WEBSOCKET_POLICY = TOKEN_POLICY


def includeme(config):

    # Set up authsanity
    settings = config.registry.settings
    settings['authsanity.source'] = 'cookie'
    settings['authsanity.cookie.max_age'] = 2592000
    settings['authsanity.cookie.httponly'] = True
    settings['authsanity.secret'] = derive_key(settings['secret_key'],
                                               settings['secret_salt'],
                                               b'h.auth.cookie_secret')
    config.include('pyramid_authsanity')

    if config.registry.settings.get('h.proxy_auth'):
        # Set a proxy authentication policy instead of the default policy
        log.warning('Enabling proxy authentication mode: you MUST ensure that '
                    'the X-Forwarded-User request header can ONLY be set by '
                    'trusted downstream reverse proxies! Failure to heed this '
                    'warning will result in ALL DATA stored by this service '
                    'being available to ANYONE!')
        config.set_authentication_policy(PROXY_POLICY)

    else:
        # Set the default authentication policy. This can be overridden by modules
        # that include this one.
        config.set_authentication_policy(DEFAULT_POLICY)

    # Allow retrieval of the authority from the request object.
    config.add_request_method(default_authority, name='default_authority', reify=True)

    # Allow retrieval of the auth token (if present) from the request object.
    config.add_request_method('.tokens.auth_token', reify=True)
