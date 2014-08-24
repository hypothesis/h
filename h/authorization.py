# -*- coding: utf-8 -*-
"""
OAuth authorization integration.

Pyramid is not easily aligned with OAuth authorization. The reason for this is
that the :class:`pyramid.interfaces.IAuthorizationPolicy` APIs do not receive
the request object. As a result, evaluation of the OAuth context is done in
during authentication. For details, see :class:`h.authentication`.

.. NOTE:: There is no provided capability for securing contexts or views using
the OAuth scopes yet.

Supported grant types
---------------------

- The client credentials grant is the only grant type. It uses the provided
  ``client_id`` and ``client_secret`` request parameters. Otherwise, the Web
  client is assumed and it is authenticated using the session, with the
  cross-site request forgery token provided in the ``assertion`` parameter.

Supported token types
---------------------

- A bearer token implementation is provided by the :mod:`h.oauth.tokens` module
  which generates Annotator-compatible access tokens. The request validator
  configured here is written to work with these.

Limitations
-----------

Almost no support for 3rd party applications exists yet. Applications can use
their client credentials, but they do not confer any authorizations and no
mechanism exists yet for users to grant authorizations to clients.
"""
from annotator import auth
from oauthlib.oauth2 import ClientCredentialsGrant
from oauthlib.oauth2 import RequestValidator as _RequestValidator
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.exceptions import BadCSRFToken
from pyramid.session import check_csrf_token

from .oauth import AnnotatorToken
from .security import WEB_SCOPES


try:
    # pylint: disable=no-name-in-module
    from hmac import compare_digest as is_equal
except ImportError:
    def is_equal(lhs, rhs):
        """Returns True if the two strings are equal, False otherwise.

        The comparison is based on a common implementation found in Django.
        This version avoids a short-circuit even for unequal lengths to reveal
        as little as possible. It takes time proportional to the length of its
        second argument.
        """
        result = 0 if len(lhs) == len(rhs) else 1
        lhs = lhs.ljust(len(rhs))
        for x, y in zip(lhs, rhs):
            result |= ord(x) ^ ord(y)
        return result == 0


def is_web_client(request, client_id):
    return client_id == request.registry.web_client.client_id


class RequestValidator(_RequestValidator):

    """
    A :class:`oauthlib.oauth2.RequestValidator` integration for h.

    This class utilizes the active :class:`h.interfaces.IClientClass` for
    authenticating clients. At this time, only client credentials and
    bearer tokens are supported. The client credentials can be implied by a
    valid authentication session.
    """

    def authenticate_client(self, request):
        if request.client_id is None and request.client_secret is None:
            try:
                check_csrf_token(request, token='assertion')
            except BadCSRFToken:
                return False
            client = request.registry.web_client
        else:
            client = request.get_client(request.client_id)

            if client is None:
                return False

            if not is_equal(client.client_secret, request.client_secret):
                return False

        request.client = client
        return True

    def get_default_scopes(self, client_id, request):
        if is_web_client(request, client_id):
            return WEB_SCOPES
        else:
            return []

    def save_bearer_token(self, token, request):
        # TODO: 3rd party authorizations
        # ------------------------------
        # Save authorizations so that they can be revoked so that access tokens
        # can be granted through non-interactive authorization flows, such as
        # refresh tokens and JWT bearer token grants.
        pass

    def validate_bearer_token(self, token, scopes, request):
        if token is None:
            return False
        client = request.registry.web_client
        ttl = auth.DEFAULT_TTL
        try:
            token = auth.decode_token(token, client.client_secret, ttl)
        except auth.TokenInvalid:
            return False
        request.client = client  # TODO: 3rd party authorizations
        request.user = token.get('userId')
        request.scopes = token.get('scopes', [])
        return True

    def validate_grant_type(self, client_id, grant_type, client, request):
        return True

    def validate_scopes(self, client_id, scopes, client, request):
        if scopes is None:
            return True

        if is_web_client(request, client_id):
            return set(scopes) <= set(WEB_SCOPES)
        else:
            # TODO: 3rd party authorizations
            return set(scopes) <= set([])


def includeme(config):
    config.include('.oauth')

    request_validator = RequestValidator()
    config.add_grant_type(ClientCredentialsGrant, 'client_credentials',
                          request_validator=request_validator)
    config.add_token_type(AnnotatorToken, request_validator=request_validator)

    # Configure the authorization policy
    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)
