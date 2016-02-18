# -*- coding: utf-8 -*-

"""Authentication and authorization configuration."""

from h.auth.util import effective_principals

__all__ = ('effective_principals',)


def auth_domain(request):
    """Return the value of the h.auth_domain config settings.

    Falls back on returning request.domain if h.auth_domain isn't set.

    """
    return request.registry.settings.get('h.auth_domain', request.domain)


def includeme(config):
    # Allow retrieval of the auth_domain from the request object.
    config.add_request_method(auth_domain, name='auth_domain', reify=True)

    # Set up pyramid authentication and authorization policies. See the Pyramid
    # documentation at:
    #
    #   http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/security.html
    #
    from h.auth.policy import AuthenticationPolicy
    from pyramid.authorization import ACLAuthorizationPolicy
    config.set_authentication_policy(AuthenticationPolicy())
    config.set_authorization_policy(ACLAuthorizationPolicy())
