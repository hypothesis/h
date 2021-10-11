"""Security configuration."""

import logging

from h.security.encryption import (  # noqa:F401
    derive_key,
    password_context,
    token_urlsafe,
)
from h.security.identity import Identity  # noqa:F401
from h.security.permissions import Permission  # noqa:F401
from h.security.permits import identity_permits
from h.security.policy import BearerTokenPolicy, SecurityPolicy

# We export this for the websocket to use as it's main policy
__all__ = ("BearerTokenPolicy",)


log = logging.getLogger(__name__)


def includeme(config):  # pragma: no cover
    config.include("h.security.request_methods")

    settings = config.registry.settings

    settings["h_auth_cookie_secret"] = derive_key(
        settings["secret_key"], settings["secret_salt"], b"h.auth.cookie_secret"
    )

    # Set the default authentication policy. This can be overridden by modules
    # that include this one.

    proxy_auth = config.registry.settings.get("h.proxy_auth")
    if proxy_auth:
        log.warning(
            "Enabling proxy authentication mode: you MUST ensure that "
            "the X-Forwarded-User request header can ONLY be set by "
            "trusted downstream reverse proxies! Failure to heed this "
            "warning will result in ALL DATA stored by this service "
            "being available to ANYONE!"
        )

    config.set_security_policy(SecurityPolicy(proxy_auth=proxy_auth))
