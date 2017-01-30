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

    @classmethod
    def get_by_refresh_token(cls, session, refresh_token):
        """
        Return the token with the given refresh token (there can be only one).

        Return None if there's no token with the given refresh_token.

        """
        return (session.query(cls)
                .filter_by(refresh_token=refresh_token)
                .order_by(cls.created.desc())
                .first())

    @classmethod
    def get_dev_token_by_userid(cls, session, userid):
        return (session.query(cls)
                .filter_by(userid=userid, authclient=None)
                .order_by(cls.created.desc())
                .first())

    def regenerate(self):
        self.value = self.prefix + security.token_urlsafe()
