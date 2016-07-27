# -*- coding: utf-8 -*-

"""Authentication configuration."""

from h.auth.policy import AuthenticationPolicy

__all__ = ()


def auth_domain(request):
    """Return the value of the h.auth_domain config settings.

    Falls back on returning request.domain if h.auth_domain isn't set.

    """
    return request.registry.settings.get('h.auth_domain', request.domain)


def includeme(config):
    # Allow retrieval of the auth_domain from the request object.
    config.add_request_method(auth_domain, name='auth_domain', reify=True)

    # Set the default authentication policy. This can be overridden by modules
    # that include this one.
    config.set_authentication_policy(AuthenticationPolicy())
