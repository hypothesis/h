# -*- coding: utf-8 -*-
"""This module exposes Annotator Auth as OAuthLib bearer tokens."""
from annotator.auth import DEFAULT_TTL, encode_token
from oauthlib import oauth2


def token_generator(request):
    """
    Generate a token from a request.

    The request must have the ``client`` and `extra_credentials`` properties
    added by OAuthLib, and a ``user`` (possibly ``None``).
    """
    client = request.client
    credentials = request.extra_credentials or {}

    credentials.setdefault('ttl', DEFAULT_TTL)
    credentials.setdefault('consumerKey', client.client_id)

    if request.user is not None:
        credentials.setdefault('userId', request.user)

    return encode_token(credentials, client.client_secret)


class AnnotatorToken(oauth2.BearerToken):

    """
    An implementation of :class:`oauthlib.oauth2.BearerToken` for Annotator.

    Uses the ``X-Annotator-Auth-Token`` header for the bearer token.
    TODO: move to the standard Authorization header.
    """

    def __init__(self, request_validator=None):
        super(AnnotatorToken, self).__init__(
            request_validator=request_validator,
            token_generator=token_generator,
            expires_in=DEFAULT_TTL,
        )

    def validate_request(self, request):
        token = request.headers.get('X-Annotator-Auth-Token')
        return self.request_validator.validate_bearer_token(
            token, request.scopes, request)

    def estimate_type(self, request):
        if 'X-Annotator-Auth-Token' in request.headers:
            return 0
        else:
            return 9
