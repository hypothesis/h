# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import hmac

from oauthlib.oauth2 import InvalidClientIdError, RequestValidator
from sqlalchemy.exc import StatementError

from h import models
from h.models.auth_client import GrantType as AuthClientGrantType
from h.util.db import lru_cache_in_transaction

AUTHZ_CODE_TTL = datetime.timedelta(minutes=10)
DEFAULT_SCOPES = ['annotation:read', 'annotation:write']


class Client(object):
    """A wrapper which responds to `client_id` which oauthlib expects in `request.client`."""
    def __init__(self, authclient):
        self.authclient = authclient
        self.client_id = authclient.id


class OAuthValidatorService(RequestValidator):
    """
    Validates OAuth requests

    This implements the ``oauthlib.oauth2.RequestValidator`` interface.
    """

    def __init__(self, session, user_svc):
        self.session = session
        self.user_svc = user_svc

        self._cached_find_authz_code = lru_cache_in_transaction(self.session)(self._find_authz_code)
        self._cached_find_client = lru_cache_in_transaction(self.session)(self._find_client)
        self._cached_find_refresh_token = lru_cache_in_transaction(self.session)(self._find_refresh_token)

    def authenticate_client(self, request, *args, **kwargs):
        """Authenticates a client, returns True if the client exists and its secret matches the request."""
        client = self.find_client(request.client_id)

        if client is None:
            return False

        if not hmac.compare_digest(client.secret, request.client_secret):
            return False

        request.client = Client(client)
        return True

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        """Authenticates a client_id, returns True if the client_id exists."""
        client = self.find_client(client_id)

        if client is None:
            return False

        request.client = Client(client)
        return True

    def client_authentication_required(self, request, *args, **kwargs):
        """
        Determine if client authentication is required for an access token request.

        Confidential clients usually require client authentication.
        Except there is a special case where a token which initially used the JWT bearer
        grant type, which only works with confidential clients, can be refreshed
        without requiring client authentication.
        """

        client = self.find_client(request.client_id)
        if client is None:
            # `authenticate_client_id` will not authenticate a missing client.
            return False

        if (request.grant_type == 'refresh_token' and
                client.grant_type == AuthClientGrantType.jwt_bearer):
            return False

        return (client.secret is not None)

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, *args, **kwargs):
        """
        Validate that the redirect_uri didn't get tampered with.

        RFC 6749 mandates checking the ``redirect_uri`` from when an authorization
        code gets created to when it is getting exchanged for an access token.
        The client can pass a ``redirect_uri`` in the token request, this should then
        be checked against the one that was used in the authorization request.

        We don't support non-registered redirect uris where the client can decide
        when it is doing the authorization request, so we just check that if the
        ``redirect_uri`` was included in the token request it matches the
        registered ``redirect_uri`` of the client.
        """
        if not redirect_uri:
            return True

        return (redirect_uri == client.authclient.redirect_uri)

    def find_authz_code(self, code):
        return self._cached_find_authz_code(code)

    def find_client(self, id_):
        return self._cached_find_client(id_)

    def find_refresh_token(self, value):
        return self._cached_find_refresh_token(value)

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        """Returns the ``redirect_uri`` stored on the client with the given id."""

        client = self.find_client(client_id)
        if client is not None:
            return client.redirect_uri

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        """Return the default scopes for the provided client."""
        return DEFAULT_SCOPES

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        """As we don't supports scopes, this returns the default scopes."""
        return self.get_default_scopes(self, request.client_id, request)

    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
        """Delete authorization code once it has been exchanged for an access token."""
        authz_code = self.find_authz_code(code)
        if authz_code:
            self.session.delete(authz_code)

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        client = self.find_client(client_id)
        if client is None:
            raise InvalidClientIdError()

        codestr = code.get('code')
        expires = utcnow() + AUTHZ_CODE_TTL
        authzcode = models.AuthzCode(user=request.user,
                                     authclient=client,
                                     expires=expires,
                                     code=codestr)
        self.session.add(authzcode)
        return authzcode

    def save_bearer_token(self, token, request, *args, **kwargs):
        """Saves a generated bearer token for the authenticated user to the database."""
        oauth_token = models.Token(userid=request.user.userid,
                                   value=token['access_token'],
                                   refresh_token=token['refresh_token'],
                                   expires=(utcnow() + datetime.timedelta(seconds=token['expires_in'])),
                                   authclient=request.client.authclient)
        self.session.add(oauth_token)
        return oauth_token

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """Checks if the provided client_id belongs to a valid AuthClient."""

        client = self.find_client(client_id)
        return (client is not None)

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        """
        Validate an authorization code.

        Check that the authorization code supplied with an access token request
        a) exists, b) has not expired, and c) is associated with the client
        identified in the request. If we return True from this function, we can
        assume that it is safe to issue an access token fo the requesting client.

        This function also finds the user associated with the given authorization
        code, and sets it on the given oauth reques object as the ``user`` property.
        It also finds the scopes associated with the authorization code, and sets it
        as well on the request object as ``scopes``.
        """
        authz_code = self.find_authz_code(code)
        if authz_code is None:
            return False

        if authz_code.expires < utcnow():
            return False

        if authz_code.authclient.id != client_id:
            return False

        request.user = authz_code.user
        request.scopes = self.get_default_scopes(client_id, request)

        return True

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        """Validates that the given client is allowed to use the give grant type."""
        if client.authclient.grant_type is None:
            return False

        if grant_type == 'refresh_token':
            return True

        return (grant_type == client.authclient.grant_type.value)

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        """Validate that the provided ``redirect_uri`` matches the one stored on the client."""

        client = self.find_client(client_id)
        if client is not None:
            return (client.redirect_uri == redirect_uri)
        return False

    def validate_refresh_token(self, refresh_token, client, request, *args, **kwargs):
        """
        Validate a supplied refresh token.

        Check that the refresh token supplied with an access token request a) exists,
        b) has not expired, and c) is associated with the client identified in the request.
        If we return True from this function, we can assume that it is safe to issue a
        new access token to the requesting client.

        This function also finds the user associated with the given refresh token, and sets
        it on the given oauth request object as the ``user`` property.
        """
        token = self.find_refresh_token(refresh_token)

        if not token or token.expired or token.authclient.id != client.client_id:
            return False

        request.user = self.user_svc.fetch(token.userid)
        return True

    def validate_response_type(self, client_id, response_type, request, *args, **kwargs):
        """Validate that the provided ``response_type`` matches the one stored on the client."""

        client = self.find_client(client_id)
        if client is not None:
            return (client.response_type is not None and
                    client.response_type.value == response_type)
        return False

    def validate_scopes(self, client_id, scopes, request, *args, **kwargs):
        """Validate that the provided `scope(s)` matches the ones stored on the client."""

        # We only allow the (dummy) default scopes for now.
        default_scopes = self.get_default_scopes(client_id, request, *args, **kwargs)
        return (scopes == default_scopes)

    def _find_authz_code(self, code):
        if code is None:
            return None

        return (self.session.query(models.AuthzCode)
                            .filter_by(code=code)
                            .one_or_none())

    def _find_client(self, id_):
        if id_ is None:
            return None

        try:
            return self.session.query(models.AuthClient).get(id_)
        except StatementError:
            return None

    def _find_refresh_token(self, value):
        if value is None:
            return None

        return (self.session.query(models.Token)
                    .filter_by(refresh_token=value)
                    .order_by(models.Token.created.desc())
                    .first())


def oauth_validator_service_factory(context, request):
    """Return a OAuthValidator instance for the passed context and request."""
    user_svc = request.find_service(name='user')
    return OAuthValidatorService(request.db, user_svc)


def utcnow():
    return datetime.datetime.utcnow()
