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
from h.security.policy.top_level import BearerTokenPolicy, TopLevelPolicy

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
    config.set_security_policy(TopLevelPolicy())
