# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import jwt
from pyramid_authsanity import interfaces
import sqlalchemy as sa
from zope import interface

from h import models
from h.exceptions import OAuthTokenError
from h.auth.util import principals_for_user
from h._compat import text_type

TICKET_TTL = datetime.timedelta(days=7)

# We only want to update the `expires` column when the tickets `expires` is at
# least one minute smaller than the potential new value. This prevents that we
# update the `expires` column on every single request.
TICKET_REFRESH_INTERVAL = datetime.timedelta(minutes=1)

# TTL of an OAuth token
TOKEN_TTL = datetime.timedelta(hours=1)


class AuthTicketNotLoadedError(Exception):
    pass


@interface.implementer(interfaces.IAuthService)
class AuthTicketService(object):
    def __init__(self, session, user_service):
        self.session = session
        self.usersvc = user_service

        self._userid = None

    def userid(self):
        """
        Return current userid, or None.

        Raises ``AuthTicketNotLoadedError`` when auth ticket has not been
        loaded yet, which signals the auth policy to call ``verify_ticket``.
        """

        if self._userid is None:
            raise AuthTicketNotLoadedError('auth ticket is not loaded yet')

        return self._userid

    def groups(self):
        """Returns security principals of the logged-in user."""

        if self._userid is None:
            raise AuthTicketNotLoadedError('auth ticket is not loaded yet')

        user = self.usersvc.fetch(self._userid)
        return principals_for_user(user)

    def verify_ticket(self, principal, ticket_id):
        """
        Verifies an authentication claim (usually extracted from a cookie)
        against the stored tickets.

        This will only successfully verify a ticket when it is found in the
        database, the principal is the same, and it hasn't expired yet.
        """

        if ticket_id is None:
            return False

        ticket = self.session.query(models.AuthTicket) \
            .filter(models.AuthTicket.id == ticket_id,
                    models.AuthTicket.user_userid == principal,
                    models.AuthTicket.expires > sa.func.now()) \
            .one_or_none()

        if ticket is None:
            return False

        self._userid = ticket.user_userid

        # We don't want to update the `expires` column of an auth ticket on
        # every single request, but only when the ticket hasn't been touched
        # within a the defined `TICKET_REFRESH_INTERVAL`.
        if (utcnow() - ticket.updated) > TICKET_REFRESH_INTERVAL:
            ticket.expires = utcnow() + TICKET_TTL

        return True

    def add_ticket(self, principal, ticket_id):
        """Store a new ticket with the given id and principal in the database."""

        user = self.usersvc.fetch(principal)
        if user is None:
            raise ValueError('Cannot find user with userid %s' % principal)

        ticket = models.AuthTicket(id=ticket_id,
                                   user=user,
                                   user_userid=user.userid,
                                   expires=(utcnow() + TICKET_TTL))
        self.session.add(ticket)
        # We cache the new userid, this will allow us to migrate the old
        # session policy to this new ticket policy.
        self._userid = user.userid

    def remove_ticket(self, ticket_id):
        """Delete a ticket by id from the database."""

        if ticket_id:
            self.session.query(models.AuthTicket).filter_by(id=ticket_id).delete()
        self._userid = None


class OAuthService(object):
    def __init__(self, session, user_service, domain):
        self.session = session
        self.usersvc = user_service
        self.domain = domain

    def verify_jwt_bearer(self, assertion, grant_type):
        """
        Verifies a JWT bearer grant token and returns the matched user.

        This adheres to RFC7523 [1] ("JSON Web Token (JWT) Profile for
        OAuth 2.0 Client Authentication and Authorization Grants").

        [1]: https://tools.ietf.org/html/rfc7523

        :param assertion: the assertion param (typically from ``request.POST``).
        :type assertion: text_type

        :param grant_type: the grant type (typically from ``request.POST``).
        :type grant_type: text_type

        :raises h.exceptions.OAuthTokenError: if the given request and/or JWT claims are invalid

        :returns: a tuple with the user and authclient
        :rtype: tuple
        """
        if grant_type != 'urn:ietf:params:oauth:grant-type:jwt-bearer':
            raise OAuthTokenError('specified grant type is not supported',
                                  'unsupported_grant_type')

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

        return (user, authclient)

    def create_token(self, user, authclient):
        """
        Creates a token for the passed-in user without any additional
        verification.

        It is the caller's responsibility to verify the token request, e.g. with
        ``verify_jwt_bearer``.

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


def auth_ticket_service_factory(context, request):
    """Return a AuthTicketService instance for the passed context and request."""
    user_service = request.find_service(name='user')
    return AuthTicketService(request.db, user_service)


def oauth_service_factory(context, request):
    """Return a OAuthService instance for the passed context and request."""
    user_service = request.find_service(name='user')
    return OAuthService(request.db, user_service, request.domain)


def utcnow():
    return datetime.datetime.utcnow()
