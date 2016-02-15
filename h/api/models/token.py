# -*- coding: utf-8 -*-
import binascii
import os

import sqlalchemy

from h.api import db
from h.api.db import mixins


#: A prefix that identifies a token as a long-lived API token
#: (as opposed to, for example, one of the short-lived JWTs that the client
#: uses).
API_TOKEN_PREFIX = u'6879-'


def unique_id():
    """Return a unique id suitable for use as the value of an API token."""
    return API_TOKEN_PREFIX + binascii.hexlify(os.urandom(16))


class Token(db.Base, mixins.Timestamps):

    """A long-lived API token for a user."""

    __tablename__ = 'token'

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
        self.value = unique_id()

    @classmethod
    def get_by_userid(cls, userid):
        return cls.query.filter(cls.userid == userid).first()

    @classmethod
    def get_by_value(cls, value):
        return cls.query.filter(cls.value == value).first()

    def regenerate(self):
        self.value = unique_id()
