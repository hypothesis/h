"""Authentication configuration."""

from h.auth.util import default_authority


def includeme(config):  # pragma: no cover
    # Allow retrieval of the authority from the request object.
    config.add_request_method(default_authority, name="default_authority", reify=True)
