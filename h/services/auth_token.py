# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import jwt

from h import models
from h.auth.tokens import LegacyClientJWT, Token


class AuthTokenService(object):
    def __init__(self, session, client_secret):
        self._session = session
        self._client_secret = client_secret

        self._validate_cache = {}

    def validate(self, token_str):
        """
        Load and validate a token.

        This will return a token object implementing
        ``h.auth.interfaces.IAuthenticationToken``, or ``None`` when the token
        cannot be found, is not a legacy JWT token, or is not valid.

        :param token_str: the token string
        :type token_str: unicode

        :returns: the token object, if found and valid, or ``None``.
        """

        if token_str in self._validate_cache:
            return self._validate_cache[token_str]

        token = self._fetch_token(token_str)
        self._validate_cache[token_str] = token
        if token is not None and token.is_valid():
            return token
        return None

    def _fetch_token(self, token_str):
        token_model = (self._session.query(models.Token)
                       .filter_by(value=token_str)
                       .one_or_none())
        if token_model is not None:
            token = Token(token_model)
            return token

        # If we've got this far it's possible the token is a legacy client JWT.
        return _maybe_jwt(token_str, self._client_secret)


def auth_token_service_factory(context, request):
    client_secret = request.registry.settings['h.client_secret']
    return AuthTokenService(request.db, client_secret)


def _maybe_jwt(token, client_secret):
    try:
        return LegacyClientJWT(token, key=client_secret)
    except jwt.InvalidTokenError:
        return None
