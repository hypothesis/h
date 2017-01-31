# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import jwt
import sqlalchemy as sa

from h import models
from h.exceptions import OAuthTokenError
from h._compat import text_type

# TTL of an OAuth token
TOKEN_TTL = datetime.timedelta(hours=1)


class OAuthService(object):
    def __init__(self, session, user_service, domain):
        self.session = session
        self.usersvc = user_service
        self.domain = domain

    def verify_token_request(self, body):
        """
        Verify an OAuth request for an access token.

        Verify either a jwt-bearer or a refresh_token request, based on the
        grant_type.

        :param body: the body of the access token request
        :type body: dict-like

        :returns: a (models.User, models.AuthClient) tuple if the request is
            valid

        :raises OAuthTokenError: if the request is invalid

        """
        grant_type = body.get('grant_type')

        verifiers = {
            'urn:ietf:params:oauth:grant-type:jwt-bearer': self._verify_jwt_bearer,
            'refresh_token': self._verify_refresh_token,
        }

        try:
            verifier = verifiers[grant_type]
        except KeyError:
            raise OAuthTokenError('specified grant type is not supported',
                                  'unsupported_grant_type')

        return verifier(body)

    def _verify_jwt_bearer(self, body):
        """
        Verifies a JWT bearer grant token and returns the matched user.

        This adheres to RFC7523 [1] ("JSON Web Token (JWT) Profile for
        OAuth 2.0 Client Authentication and Authorization Grants").

        [1]: https://tools.ietf.org/html/rfc7523

        :param body: the body of the access token request
        :type body: dict-like

        :raises h.exceptions.OAuthTokenError: if the given request and/or JWT claims are invalid

        :returns: a tuple with the user and authclient
        :rtype: tuple
        """
        assertion = body.get('assertion')

        if not assertion or type(assertion) != text_type:
            raise OAuthTokenError('required assertion parameter is missing',
                                  'invalid_request')
        token = assertion

        unverified_claims = self._decode(token, verify=False)

        client_id = unverified_claims.get('iss', None)
        if not client_id:
            raise OAuthTokenError('grant token issuer is missing', 'invalid_grant')

        authclient = None
        try:
            authclient = self.session.query(models.AuthClient).get(client_id)
        except sa.exc.StatementError as exc:
            if str(exc.orig) == 'badly formed hexadecimal UUID string':
                pass
            else:
                raise
        if not authclient:
            raise OAuthTokenError('given JWT issuer is invalid', 'invalid_grant')

        claims = self._decode(token,
                              algorithms=['HS256'],
                              audience=self.domain,
                              key=authclient.secret,
                              leeway=10)

        userid = claims.get('sub')
        if not userid:
            raise OAuthTokenError('JWT subject is missing', 'invalid_grant')

        user = self.usersvc.fetch(userid)
        if user is None:
            raise OAuthTokenError('user with userid described in subject could not be found',
                                  'invalid_grant')

        if user.authority != authclient.authority:
            raise OAuthTokenError('authenticated client and JWT subject authorities do not match',
                                  'invalid_grant')

        return (user, authclient)

    def _verify_refresh_token(self, body):
        refresh_token = body.get('refresh_token')

        if not refresh_token:
            raise OAuthTokenError('required refresh_token parameter is missing',
                                  'invalid_request')

        if type(refresh_token) != text_type:
            raise OAuthTokenError('refresh_token is invalid', 'invalid_refresh')

        token = (self.session.query(models.Token)
                 .filter_by(refresh_token=refresh_token)
                 .order_by(models.Token.created.desc())
                 .first())

        if not token:
            raise OAuthTokenError('refresh_token is invalid', 'invalid_refresh')

        if token.expired:
            raise OAuthTokenError('refresh_token has expired', 'invalid_refresh')

        user = self.usersvc.fetch(token.userid)
        if not user:
            raise OAuthTokenError('user no longer exists', 'invalid_refresh')

        return (user, token.authclient)

    def create_token(self, user, authclient):
        """
        Creates a token for the passed-in user without any additional
        verification.

        It is the caller's responsibility to verify the token request, e.g. with
        ``verify_token_request``.

        :param assertion: the user for whom the token should be created.
        :type assertion: h.models.User

        :rtype: h.models.Token
        """
        token = models.Token(userid=user.userid,
                             expires=(utcnow() + TOKEN_TTL),
                             authclient=authclient)
        self.session.add(token)

        return token

    def _decode(self, token, **kwargs):
        try:
            claims = jwt.decode(token, **kwargs)
            return claims
        except jwt.DecodeError:
            raise OAuthTokenError('invalid JWT signature', 'invalid_grant')
        except jwt.exceptions.InvalidAlgorithmError:
            raise OAuthTokenError('invalid JWT signature algorithm', 'invalid_grant')
        except jwt.MissingRequiredClaimError as exc:
            raise OAuthTokenError('JWT is missing claim %s' % exc.claim, 'invalid_grant')
        except jwt.InvalidAudienceError:
            raise OAuthTokenError('invalid JWT audience', 'invalid_grant')
        except jwt.ImmatureSignatureError:
            raise OAuthTokenError('JWT not before is in the future', 'invalid_grant')
        except jwt.ExpiredSignatureError:
            raise OAuthTokenError('JWT token is expired', 'invalid_grant')
        except jwt.InvalidIssuedAtError:
            raise OAuthTokenError('JWT issued at is in the future', 'invalid_grant')


def oauth_service_factory(context, request):
    """Return a OAuthService instance for the passed context and request."""
    user_service = request.find_service(name='user')
    return OAuthService(request.db, user_service, request.domain)


def utcnow():
    return datetime.datetime.utcnow()
