# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import binascii
import datetime
import os

import sqlalchemy
from sqlalchemy.dialects import postgresql

from h.auth.interfaces import IAuthenticationToken
from h.db import Base
from h.db import mixins


class Token(Base, mixins.Timestamps):

    """A long-lived API token for a user."""

    __tablename__ = 'token'

    #: A prefix that identifies a token as a long-lived API token (as opposed
    #: to, for example, one of the short-lived JWTs that the client uses).
    prefix = u'6879-'

    #: A prefix that identifies a token as a refresh token.
    refresh_token_prefix = u'7980-'

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

    def __init__(self, expires=None, **kwargs):
        super(Token, self).__init__(expires=expires, **kwargs)
        self.regenerate()

        if expires:
            self.refresh_token = self.refresh_token_prefix + _token()

    @classmethod
    def get_dev_token_by_userid(cls, session, userid):
        return (session.query(cls)
                .filter_by(userid=userid, authclient=None)
                .order_by(cls.created.desc())
                .first())

    def regenerate(self):
        self.value = self.prefix + _token()


def _token():
    """Return a random string suitable for use in an API token."""
    return binascii.hexlify(os.urandom(16))
