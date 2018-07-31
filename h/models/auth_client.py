# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import enum
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.hybrid import hybrid_property, Comparator

from h.db import Base
from h.db.mixins import Timestamps
from h.util.auth_client import split_client
from h._compat import string_types


class ClientIDComparator(Comparator):
    """
    Custom comparator for :py:attr:`~h.models.auth_client.AuthClient.clientid`.

    Generate valid SQL queries for this compound attribute.

    See :py:class:`h.models.user.UserIDComparator` for extended details
    """
    def __init__(self, id, authority):
        self.id = id
        self.authority = authority

    def __clause_element__(self):
        return sa.tuple_(self.id, self.authority)

    def __eq__(self, other):
        if isinstance(other, string_types):
            try:
                val = split_client(other)
            except ValueError:
                # The value being compared isn't a valid clientid
                return False
            else:
                other = sa.tuple_(val['id'],
                                  val['authority'])
        return self.__clause_element__() == other

    def in_(self, clientids):
        others = []
        for clientid in clientids:
            try:
                val = split_client(clientid)
            except ValueError:
                continue

            other = sa.tuple_(val['id'], val['authority'])
            others.append(other)

        if not others:
            return False

        return self.__clause_element__().in_(others)


class GrantType(enum.Enum):
    """
    Allowable grant types for an :class:`AuthClient`.

    The grant type defines the credentials that are presented to the OAuth
    access token endpoint in order to prove that the client is authorized for
    a specified user.
    """
    # N.B. we define all the known and valid grant types from the main OAuth
    # 2.0 standard, RFC6749, as well as the extension for JWT Bearer grants
    # specified in RFC7523.
    #
    # The fact that a grant type is specified here does *not* imply that we
    # support that grant type for access token requests: it's just so we can
    # avoid having to change this ENUM type in Postgres every time we add
    # support for a new grant type.

    #: Authorization code grant. Used when exchanging an authorization code
    #: for an access token.
    authorization_code = 'authorization_code'

    #: Client credentials grant. Used when a client wants to directly fetch an
    #: access token for its own purposes, rather than for a specific user.
    client_credentials = 'client_credentials'

    #: JSON Web Token Bearer grant. Used by clients which are implicitly
    #: authorized on behalf of all their users and can sign JWTs which are
    #: exchangeable for an access token.
    jwt_bearer = 'urn:ietf:params:oauth:grant-type:jwt-bearer'

    #: Resource owner credentials grant. Can be used by trusted clients that
    #: are allowed to ask users for their login credentials directly.
    password = 'password'


class ResponseType(enum.Enum):
    """
    Allowable authorization response types for an :class:`AuthClient`.

    The response type defines the response expected from our authorization
    service after a successful authorization for a client.
    """

    #: Authorization code grant, which is later exchanged for an access token.
    code = 'code'

    #: "Implicit" grant, in which an authorization request receives an access
    #: token directly.
    token = 'token'


class AuthClient(Base, Timestamps):
    """
    An OAuth client.

    An AuthClient represents an OAuth client, an entity which can access
    protected resources (such as annotations) on behalf of a user.

    The first type of OAuth client we have is a very special one, which can
    access protected resources for *any* user within its *authority*. These
    are "publisher" accounts, which can create users in our database, and
    subsequently issue grant authorization tokens for any of those users.
    """

    __tablename__ = 'authclient'
    __table_args__ = (sa.CheckConstraint("(grant_type != 'authorization_code') OR (redirect_uri IS NOT NULL)",
                                         name='authz_grant_redirect_uri'),)

    #: Public client identifier
    id = sa.Column(postgresql.UUID,
                   server_default=sa.func.uuid_generate_v1mc(),
                   primary_key=True)

    #: Human-readable name for reference.
    name = sa.Column(sa.UnicodeText, nullable=True)

    #: Client secret
    secret = sa.Column(sa.UnicodeText, nullable=True)

    #: Authority for which this client is allowed to authorize users.
    authority = sa.Column(sa.UnicodeText, nullable=False)

    #: Grant type used by this client.
    grant_type = sa.Column(sa.Enum(GrantType, name='authclient_grant_type'),
                           nullable=True)

    #: Authorization response type used by this client.
    response_type = sa.Column(sa.Enum(ResponseType, name='authclient_response_type'),
                              nullable=True)
    #: Redirect URI for OAuth 2 authorization code grant type.
    redirect_uri = sa.Column(sa.UnicodeText, nullable=True)

    #: Is this client trusted? That is, is this client one that we control?
    #: Trusted clients don't require explicit authorization from a user.
    trusted = sa.Column(sa.Boolean,
                        default=False,
                        server_default=sa.sql.expression.false(),
                        nullable=False)

    @hybrid_property
    def clientid(self):
        return 'client:{id}@{authority}'.format(id=self.id,
                                                authority=self.authority)

    @clientid.comparator
    def clientid(cls):  # noqa: N805
        return ClientIDComparator(cls.id, cls.authority)

    def __repr__(self):
        return 'AuthClient(id={self.id!r})'.format(self=self)
