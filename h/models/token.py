# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import binascii
import datetime
import os

import sqlalchemy
from sqlalchemy.dialects import postgresql

from h import security
from h.auth.interfaces import IAuthenticationToken
from h.db import Base
from h.db import mixins


class Token(Base, mixins.Timestamps):

    """A long-lived API token for a user."""

    __tablename__ = 'token'

    #: A prefix that identifies a token as a long-lived API token (as opposed
    #: to, for example, one of the short-lived JWTs that the client uses).
    prefix = u'6879-'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           autoincrement=True,
                           primary_key=True)

    userid = sqlalchemy.Column(sqlalchemy.UnicodeText(),
                               nullable=False)

    value = sqlalchemy.Column(sqlalchemy.UnicodeText(),
                              nullable=False,
                              unique=True)

    #: A timestamp after which this token will no longer be considered valid.
    #: A NULL value in this column indicates a token that does not expire.
    expires = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)

    #: A refresh token that can be exchanged for a new token (with a new value
    #: and expiry time). A NULL value in this column indicates a token that
    #: cannot be refreshed.
    refresh_token = sqlalchemy.Column(sqlalchemy.UnicodeText(),
                                      unique=True,
                                      nullable=True)

    _authclient_id = sqlalchemy.Column('authclient_id',
                                       postgresql.UUID(),
                                       sqlalchemy.ForeignKey('authclient.id', ondelete='cascade'),
                                       nullable=True)

    #: The authclient which created the token.
    #: A NULL value means it is a developer token.
    authclient = sqlalchemy.orm.relationship('AuthClient')

    def __init__(self, **kwargs):
        super(Token, self).__init__(**kwargs)
        self.regenerate()

        if self.expires:
            self.refresh_token = security.token_urlsafe()

    @property
    def expired(self):
        """True if this token has expired, False otherwise."""
        return self.expires and datetime.datetime.utcnow() > self.expires

    @property
    def ttl(self):
        """The amount of time from now until this token expires, in seconds."""
        if not self.expires:
            return None

        now = datetime.datetime.utcnow()
        ttl = self.expires - now
        ttl_in_seconds = ttl.total_seconds()
        # We truncate (rather than round) ttl_in_seconds to get an int.
        # For example 2.3 beccomes 2, but 2.9 also becomes 2.
        ttl_in_seconds_truncated = int(ttl_in_seconds)
        return ttl_in_seconds_truncated

    @classmethod
    def get_dev_token_by_userid(cls, session, userid):
        return (session.query(cls)
                .filter_by(userid=userid, authclient=None)
                .order_by(cls.created.desc())
                .first())

    def regenerate(self):
        self.value = self.prefix + security.token_urlsafe()
