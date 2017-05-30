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
        if 'assertion' not in body:
            raise OAuthTokenError('required assertion parameter is missing',
                                  'invalid_request')

        token = GrantToken(body['assertion'])

        authclient = self._get_authclient_by_id(token.issuer)
        if not authclient:
            raise OAuthTokenError('grant token issuer (iss) is invalid', 'invalid_grant')

        verified_token = token.verified(key=authclient.secret,
                                        audience=self.domain)

        user = self.usersvc.fetch(verified_token.subject)
        if user is None:
            raise OAuthTokenError('grant token subject (sub) could not be found',
                                  'invalid_grant')

        if user.authority != authclient.authority:
            raise OAuthTokenError('grant token subject (sub) does not match issuer (iss)',
                                  'invalid_grant')

        return (user, authclient)

    def _get_authclient_by_id(self, client_id):
        try:
            return self.session.query(models.AuthClient).get(client_id)
        except sa.exc.StatementError as exc:
            if str(exc.orig) == 'badly formed hexadecimal UUID string':
                return None
            else:
                raise

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

    def create_grant_token(self, user, authclient):
        """
        Generate a JWT bearer grant token for a user.

        :param user: The user to generate the token for.
        :type user: h.models.User
        :param authclient: The OAuth client that is going to use the token.
        :type authclient: h.models.AuthClient
        """
        now = datetime.datetime.utcnow()
        claims = {
            'aud': self.domain,
            'iss': authclient.id,
            'sub': 'acct:{}@{}'.format(user.username, user.authority),
            'nbf': now,
            'exp': now + datetime.timedelta(minutes=5),
        }
        return jwt.encode(claims, authclient.secret, algorithm='HS256')


class GrantToken(object):
    """
    Represents a JWT bearer grant token.

    This class is responsible for a couple of things: firstly, verifying that
    the token is a correctly-formatted JSON Web Token, and that it contains all
    the required claims in the right formats. Some of this processing is
    deferred to the `jwt` module, but that doesn't handle all the fields we
    want to validate.

    """

    def __init__(self, token):
        self._token = token

        try:
            self._claims = jwt.decode(token, verify=False)
        except jwt.DecodeError as e:
            raise self._error('grant token format is invalid', 'invalid_request')

    @property
    def issuer(self):
        iss = self._claims.get('iss', None)
        if not iss:
            raise self._missing_field_error('iss', 'issuer')
        return iss

    def _error(self, message, error_type='invalid_grant'):
        return OAuthTokenError(message, error_type)

    def _missing_field_error(self, claim_name, claim_description=None):
        if claim_description:
            message = 'grant token {} ({}) is missing'.format(claim_description,
                                                              claim_name)
        else:
            message = 'grant token claim {} is missing'.format(claim_name)
        return self._error(message)

    def _invalid_field_error(self, claim_name, claim_description=None):
        if claim_description:
            message = 'grant token {} ({}) is invalid'.format(claim_description,
                                                              claim_name)
        else:
            message = 'grant token claim {} is invalid'.format(claim_name)
        return self._error(message)

    def verified(self, key, audience):
        return VerifiedGrantToken(self._token, key, audience)


class VerifiedGrantToken(GrantToken):
    """
    Represents a JWT bearer grant token verified with a secret key.

    This exposes more claims than the `GrantToken` superclass, so that it's not
    possible to access the subject ID without first verifying the token.

    """

    MAX_LIFETIME = datetime.timedelta(minutes=10)
    LEEWAY = datetime.timedelta(seconds=10)

    def __init__(self, token, key, audience):
        super(VerifiedGrantToken, self).__init__(token)
        self._verify(key, audience)

    def _verify(self, key, audience):
        if self.expiry - self.not_before > self.MAX_LIFETIME:
            raise self._error('grant token lifetime is too long')
        try:
            jwt.decode(self._token,
                       algorithms=['HS256'],
                       audience=audience,
                       key=key,
                       leeway=self.LEEWAY)
        except jwt.DecodeError:
            raise self._error('grant token signature is invalid')
        except jwt.exceptions.InvalidAlgorithmError:
            raise self._error('grant token signature algorithm is invalid')
        except jwt.MissingRequiredClaimError as exc:
            if exc.claim == 'aud':
                raise self._missing_field_error('aud', 'audience')
            else:
                raise self._missing_field_error(exc.claim)
        except jwt.InvalidAudienceError:
            raise self._invalid_field_error('aud', 'audience')
        except jwt.ImmatureSignatureError:
            raise self._error('grant token is not yet valid')
        except jwt.ExpiredSignatureError:
            raise self._error('grant token is expired')
        except jwt.InvalidIssuedAtError:
            raise self._error('grant token issue time (iat) is in the future')

    @property
    def expiry(self):
        return self._timestamp_claim('exp', 'expiry')

    @property
    def not_before(self):
        return self._timestamp_claim('nbf', 'start time')

    def _timestamp_claim(self, key, description):
        claim = self._claims.get(key, None)
        if claim is None:
            raise self._missing_field_error(key, description)
        try:
            return datetime.datetime.utcfromtimestamp(claim)
        except (TypeError, ValueError):
            raise self._invalid_field_error(key, description)

    @property
    def subject(self):
        sub = self._claims.get('sub', None)
        if not sub:
            raise self._missing_field_error('sub', 'subject')
        return sub


def oauth_service_factory(context, request):
    """Return a OAuthService instance for the passed context and request."""
    user_service = request.find_service(name='user')
    return OAuthService(request.db, user_service, request.domain)


def utcnow():
    return datetime.datetime.utcnow()
