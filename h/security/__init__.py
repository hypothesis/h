from h.security.acl import ACL  # noqa:F401
from h.security.encryption import (  # noqa:F401
    derive_key,
    password_context,
    token_urlsafe,
)
from h.security.identity import Identity, get_identity  # noqa:F401
from h.security.permissions import Permission  # noqa:F401
from h.security.permits import identity_permits
from h.security.principals import principals_for_identity  # noqa:F401


def includeme(config):  # pragma: no cover
    # Fake the Pyramid 2.0 identity method on requests until we upgrade
    config.add_request_method(get_identity, name="identity", reify=True)
