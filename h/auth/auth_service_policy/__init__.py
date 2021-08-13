from pyramid_authsanity.interfaces import IAuthSourceService

from h.auth.auth_service_policy.cookie_source import CookieAuthSourceInitializer
from h.auth.auth_service_policy.policy import AuthServicePolicy
from h.security import derive_key


def includeme(config):  # pragma: no cover
    settings = config.registry.settings

    config.register_service_factory(
        CookieAuthSourceInitializer(
            secret=derive_key(
                settings["secret_key"], settings["secret_salt"], b"h.auth.cookie_secret"
            ),
        ),
        iface=IAuthSourceService,
    )
