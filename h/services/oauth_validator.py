# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from oauthlib.oauth2 import InvalidClientIdError, RequestValidator
from sqlalchemy.exc import StatementError

from h import models
from h.models.auth_client import GrantType as AuthClientGrantType
from h.util.db import lru_cache_in_transaction

AUTHZ_CODE_TTL = datetime.timedelta(minutes=10)
DEFAULT_SCOPES = ['annotation:read', 'annotation:write']


class OAuthValidatorService(RequestValidator):
    """
    Validates OAuth requests

    This implements the ``oauthlib.oauth2.RequestValidator`` interface.
    """

    def __init__(self, session, user_svc):
        self.session = session
        self.user_svc = user_svc

        self._cached_find_client = lru_cache_in_transaction(self.session)(self._find_client)
        self._cached_find_refresh_token = lru_cache_in_transaction(self.session)(self._find_refresh_token)

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        """Authenticates a client_id, returns True if the client_id exists."""
        client = self.find_client(client_id)
        request.client = client
        return (client is not None)

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
                                   authclient=request.client)
        self.session.add(oauth_token)
        return oauth_token

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """Checks if the provided client_id belongs to a valid AuthClient."""

        client = self.find_client(client_id)
        return (client is not None)

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        """Validates that the given client is allowed to use the give grant type."""
        if client.grant_type is None:
            return False

        if grant_type == 'refresh_token':
            return True

        return (grant_type == client.grant_type.value)

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

        if not token or token.expired or token.authclient != client:
            return False

        request.user = self.user_svc.fetch(token.userid)
        return True

    def validate_response_type(self, client_id, response_type, request, *args, **kwargs):
        """Validate that the provided ``response_type`` matches the one stored on the client."""

        client = self.find_client(client_id)
        if client is not None:
            return (client.response_type.value == response_type)
        return False

    def validate_scopes(self, client_id, scopes, request, *args, **kwargs):
        """Validate that the provided `scope(s)` matches the ones stored on the client."""

        # We only allow the (dummy) default scopes for now.
        default_scopes = self.get_default_scopes(client_id, request, *args, **kwargs)
        return (scopes == default_scopes)

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
