"""Authentication configuration."""
import logging

from h.auth.policy import AuthenticationPolicy, TokenAuthenticationPolicy
from h.auth.util import default_authority
from h.security import derive_key

# We export this for the websocket to use as it's main policy
__all__ = ("TokenAuthenticationPolicy",)


log = logging.getLogger(__name__)


def includeme(config):  # pragma: no cover
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

    config.set_security_policy(AuthenticationPolicy(proxy_auth=proxy_auth))

    # Allow retrieval of the authority from the request object.
    config.add_request_method(default_authority, name="default_authority", reify=True)

    # Allow retrieval of the auth token (if present) from the request object.
    config.add_request_method("h.auth.tokens.auth_token", reify=True)
