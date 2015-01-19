# -*- coding: utf-8 -*-
"""
OAuth / OpenID Connect authentication integration.

This module provides an authentication policy, which is an instance of
:class:`pyramid.interfaces.IAuthenticationPolicy`, that computes an OAuth
context when the request is authenticated.

Authentication is handled by session authentication. Views can call the
``pyramid.security`` functions ``remember`` and ``forget``. When no session
authentication is found, the any token types registered using the API provided
by :mod:`pyramid_oauthlib` will be used to determine the authenticated client
and the authorized user and scopes.
"""
import base64
import os

from pyramid.authentication import SessionAuthenticationPolicy

from .authorization import WEB_SCOPES
from .oauth import IClientFactory


class OAuthPolicy(SessionAuthenticationPolicy):

    """
    Hybrid OAuth / session authentication.

    This authentication policy first checks the session authentication and
    then uses OAuth as a fallback. Afterward, the request will have attributes
    for ``client``, ``user`` and ``scope``. Any or all of them may be ``None``.
    """

    def unauthenticated_userid(self, request):
        if hasattr(request, 'user'):
            return request.user

        userid = super(OAuthPolicy, self).unauthenticated_userid(request)

        if userid is None:
            request.verify_request()
            request.client = getattr(request, 'client', None)
            request.user = getattr(request, 'user', None)
            request.scopes = getattr(request, 'scopes', None)
        else:
            request.client = request.registry.web_client
            request.user = userid
            request.scopes = WEB_SCOPES

        return request.user


def register_web_client(config):
    registry = config.registry
    settings = registry.settings

    client_factory = registry.getUtility(IClientFactory)
    client_id = settings['h.client_id']
    client_secret = settings['h.client_secret']

    if client_id is None:
        client_id = base64.urlsafe_b64encode(os.urandom(18))

    if client_secret is None:
        client_secret = base64.urlsafe_b64encode(os.urandom(18))

    registry.web_client = client_factory(client_id)
    registry.web_client.client_secret = client_secret


def includeme(config):
    config.include('.oauth')

    registry = config.registry
    settings = registry.settings

    authn_debug = settings.get('debug_authorization')
    authn_policy = OAuthPolicy(debug=authn_debug, prefix='')
    config.set_authentication_policy(authn_policy)

    client_class = settings.get('h.client_factory', 'h.models.Client')
    config.set_client_factory(client_class)
    config.action(None, register_web_client, args=(config,))
