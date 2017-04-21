# -*- coding: utf-8 -*-

"""
Authentication and authorization policies for the demo.
"""

from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

USERS = {
    'alice': 's3cret',
    'bob': 'passw0rd',
    'charlie': 'h1dden',
}


def groupfinder(username, password, request):
    if USERS.get(username) == password:
        return []
    return None


def includeme(config):
    authn_policy = BasicAuthAuthenticationPolicy(groupfinder,
                                                 realm='Demo API')
    authz_policy = ACLAuthorizationPolicy()

    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
