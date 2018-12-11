# -*- coding: utf-8 -*-

"""Authentication configuration."""
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

__all__ = ("DEFAULT_POLICY", "WEBSOCKET_POLICY")

log = logging.getLogger(__name__)

PROXY_POLICY = RemoteUserAuthenticationPolicy(
    environ_key="HTTP_X_FORWARDED_USER", callback=groupfinder
)
TICKET_POLICY = pyramid_authsanity.AuthServicePolicy()

TOKEN_POLICY = TokenAuthenticationPolicy(callback=groupfinder)
AUTH_CLIENT_POLICY = AuthClientPolicy()

API_POLICY = APIAuthenticationPolicy(
    user_policy=TOKEN_POLICY, client_policy=AUTH_CLIENT_POLICY
)

DEFAULT_POLICY = AuthenticationPolicy(
    api_policy=API_POLICY, fallback_policy=TICKET_POLICY
)
WEBSOCKET_POLICY = TOKEN_POLICY


def includeme(config):
    global DEFAULT_POLICY
    global WEBSOCKET_POLICY

    # Set up authsanity
    settings = config.registry.settings
    settings["authsanity.source"] = "cookie"
    settings["authsanity.cookie.max_age"] = 2592000
    settings["authsanity.cookie.httponly"] = True
    settings["authsanity.secret"] = derive_key(
        settings["secret_key"], settings["secret_salt"], b"h.auth.cookie_secret"
    )
    config.include("pyramid_authsanity")

    if config.registry.settings.get("h.proxy_auth"):
        log.warning(
            "Enabling proxy authentication mode: you MUST ensure that "
            "the X-Forwarded-User request header can ONLY be set by "
            "trusted downstream reverse proxies! Failure to heed this "
            "warning will result in ALL DATA stored by this service "
            "being available to ANYONE!"
        )

        DEFAULT_POLICY = AuthenticationPolicy(
            api_policy=API_POLICY, fallback_policy=PROXY_POLICY
        )
        WEBSOCKET_POLICY = TOKEN_POLICY

    # Set the default authentication policy. This can be overridden by modules
    # that include this one.
    config.set_authentication_policy(DEFAULT_POLICY)

    # Allow retrieval of the authority from the request object.
    config.add_request_method(default_authority, name="default_authority", reify=True)

    # Allow retrieval of the auth token (if present) from the request object.
    config.add_request_method(".tokens.auth_token", reify=True)
