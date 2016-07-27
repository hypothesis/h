# -*- coding: utf-8 -*-

"""Authentication configuration."""

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid_multiauth import MultiAuthenticationPolicy

from h.auth.policy import AuthenticationPolicy, TokenAuthenticationPolicy
from h.auth.util import groupfinder

__all__ = (
    'DEFAULT_POLICY',
    'WEBSOCKET_POLICY',
)

SESSION_POLICY = SessionAuthenticationPolicy(callback=groupfinder)
TOKEN_POLICY = TokenAuthenticationPolicy(callback=groupfinder)

DEFAULT_POLICY = AuthenticationPolicy(api_policy=TOKEN_POLICY,
                                      fallback_policy=SESSION_POLICY)
WEBSOCKET_POLICY = MultiAuthenticationPolicy([TOKEN_POLICY, SESSION_POLICY])


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
    config.set_authentication_policy(DEFAULT_POLICY)
