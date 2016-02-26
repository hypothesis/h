# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import binascii
import os

import sqlalchemy

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
                               nullable=False,
                               unique=True)

    value = sqlalchemy.Column(sqlalchemy.UnicodeText(),
                              nullable=False,
                              unique=True)

    def __init__(self, userid):
        self.userid = userid
        self.regenerate()

    @classmethod
    def get_by_userid(cls, userid):
        return cls.query.filter(cls.userid == userid).first()

    @classmethod
    def get_by_value(cls, value):
        return cls.query.filter(cls.value == value).first()

    def regenerate(self):
        self.value = self.prefix + _token()


def _token():
    """Return a random string suitable for use in an API token."""
    return binascii.hexlify(os.urandom(16))
