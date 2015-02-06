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
import datetime

import jwt
from oauthlib.oauth2 import BearerToken
from oauthlib.oauth2 import ClientCredentialsGrant
from oauthlib.oauth2 import RequestValidator as _RequestValidator
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.exceptions import BadCSRFToken
from pyramid.session import check_csrf_token

from .oauth import JWTBearerGrant
from .security import WEB_SCOPES

DEFAULT_TTL = 3600
LEEWAY = 240  # allowance for clock skew in verification


def is_web_client(request, client_id):
    return client_id == request.registry.web_client.client_id


def token_generator(request):
    """
    Generate a token from a request.

    The request must have the ``client`` and `extra_credentials`` properties
    added by OAuthLib, and a ``user`` (possibly ``None``).
    """
    client = request.client
    now = datetime.datetime.utcnow().replace(microsecond=0)
    ttl = datetime.timedelta(seconds=DEFAULT_TTL)

    payload = {
        'aud': request.host_url,
        'iss': client.client_id,
        'exp': now + ttl,
        'iat': now,
        'nbf': now,
    }

    if request.user is not None:
        payload['sub'] = request.user
        payload['userId'] = request.user  # bw compat

    # bw compat
    payload['issuedAt'] = now.isoformat()
    payload['ttl'] = ttl.total_seconds()
    payload['consumerKey'] = client.client_id

    credentials = getattr(request, 'extra_credentials', None)
    if credentials is not None:
        payload.update(credentials)

    return jwt.encode(payload, client.client_secret)


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

            if not jwt.constant_time_compare(
                    client.client_secret,
                    request.client_secret
            ):
                return False

        request.client = client
        return True

    def get_default_scopes(self, client_id, request):
        if is_web_client(request, client_id):
            return WEB_SCOPES
        else:
            return []

    def get_original_scopes(self, assertion, request):
        # TODO: 3rd party authorizations
        return WEB_SCOPES

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

        try:
            payload, signing_input, header, signature = jwt.load(token)
        except jwt.InvalidTokenError:
            return False

        aud = request.host_url
        iss = payload['iss']

        if is_web_client(request, iss):
            client = request.registry.web_client
            secret = client.client_secret
            scopes = WEB_SCOPES
        else:
            # TODO: 3rd party authorizations
            return False

        try:
            jwt.verify_signature(payload, signing_input, header, signature,
                                 key=secret, audience=aud, issuer=iss,
                                 leeway=LEEWAY)
        except jwt.InvalidTokenError:
            return False

        request.client = client
        request.user = payload.get('sub', None)
        request.scopes = scopes
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
    config.add_oauth_param('assertion')
    config.add_oauth_param('client_assertion')
    config.add_oauth_param('client_assertion_type')

    request_validator = RequestValidator()
    config.add_grant_type(ClientCredentialsGrant, 'client_credentials',
                          request_validator=request_validator)
    config.add_grant_type(JWTBearerGrant, JWTBearerGrant.uri,
                          request_validator=request_validator)
    config.add_token_type(BearerToken,
                          request_validator=request_validator,
                          token_generator=token_generator,
                          expires_in=DEFAULT_TTL)

    # Configure the authorization policy
    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)
