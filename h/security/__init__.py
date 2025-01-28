"""Security configuration."""

import logging

from h.security.encryption import (
    derive_key,
    password_context,
    token_urlsafe,
)
from h.security.identity import Identity
from h.security.permissions import Permission
from h.security.permits import identity_permits
from h.security.policy import StreamerPolicy, TopLevelPolicy

log = logging.getLogger(__name__)


def includeme(config):  # pragma: no cover
    config.include("h.security.request_methods")

    settings = config.registry.settings

    settings["h_auth_cookie_secret"] = derive_key(
        settings["secret_key"], settings["secret_salt"], b"h.auth.cookie_secret"
    )
    settings["h_api_auth_cookie_secret"] = derive_key(
        settings["h_api_auth_cookie_secret_key"],
        settings["h_api_auth_cookie_salt"],
        b"h_api_auth_cookie_secret",
    )

    # Set the default authentication policy. This can be overridden by modules
    # that include this one.
    config.set_security_policy(TopLevelPolicy())
