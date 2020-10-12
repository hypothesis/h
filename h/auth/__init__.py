"""Authentication configuration."""
import logging

import pyramid_authsanity
from pyramid.authentication import RemoteUserAuthenticationPolicy

from h.auth.policy import (
    APIAuthenticationPolicy,
    AuthClientPolicy,
    AuthenticationPolicy,
    TokenAuthenticationPolicy,
)
from h.auth.util import default_authority, groupfinder
from h.security import derive_key

log = logging.getLogger(__name__)

_API_POLICY = APIAuthenticationPolicy(
    user_policy=TokenAuthenticationPolicy(callback=groupfinder),
    client_policy=AuthClientPolicy(),
)

DEFAULT_POLICY = AuthenticationPolicy(
    api_policy=_API_POLICY, fallback_policy=pyramid_authsanity.AuthServicePolicy()
)


def includeme(config):
    global DEFAULT_POLICY

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
            api_policy=_API_POLICY,
            fallback_policy=RemoteUserAuthenticationPolicy(
                environ_key="HTTP_X_FORWARDED_USER", callback=groupfinder
            ),
        )

    # Set the default authentication policy. This can be overridden by modules
    # that include this one.
    config.set_authentication_policy(DEFAULT_POLICY)

    # Allow retrieval of the authority from the request object.
    config.add_request_method(default_authority, name="default_authority", reify=True)

    # Allow retrieval of the auth token (if present) from the request object.
    config.add_request_method(".tokens.auth_token", reify=True)
