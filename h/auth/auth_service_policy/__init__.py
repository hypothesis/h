from pyramid.settings import asbool
from pyramid_authsanity.interfaces import IAuthSourceService
from pyramid_authsanity.sources import CookieAuthSourceInitializer

from h.auth.auth_service_policy.policy import AuthServicePolicy
from h.security import derive_key

default_settings = (
    ("source", str, ""),
    ("debug", asbool, False),
    ("session.value_key", str, "sanity."),
)

# Stolen from pyramid_debugtoolbar
def parse_settings(settings):
    parsed = {}

    def populate(name, convert, default):
        name = "%s%s" % ("authsanity.", name)
        value = convert(settings.get(name, default))
        parsed[name] = value

    for name, convert, default in default_settings:
        populate(name, convert, default)
    return parsed


def includeme(config):  # pragma: no cover
    # Set up authsanity
    settings = config.registry.settings
    secret = derive_key(
        settings["secret_key"], settings["secret_salt"], b"h.auth.cookie_secret"
    )

    # Go parse the settings
    settings = parse_settings(config.registry.settings)

    # Update the config
    config.registry.settings.update(settings)

    # include pyramid_services
    config.include("pyramid_services")

    config.register_service_factory(
        CookieAuthSourceInitializer(
            secret,
            cookie_name="auth",
            path="/",
            domains=[],
            debug=False,
            max_age=2592000,
            httponly=True,
        ),
        iface=IAuthSourceService,
    )
