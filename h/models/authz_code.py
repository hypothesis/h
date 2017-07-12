# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from h.db import Base, mixins


class AuthzCode(Base, mixins.Timestamps):
    """An OAuth 2 authorization code."""

    __tablename__ = 'authzcode'

    #: Auth code
    id = sa.Column(sa.Integer,
                   autoincrement=True,
                   primary_key=True)

    _user_id = sa.Column('user_id',
                         sa.Integer,
                         sa.ForeignKey('user.id', ondelete='cascade'),
                         nullable=False)

    #: The user whose authorization code it is
    user = sa.orm.relationship('User')

    _authclient_id = sa.Column('authclient_id',
                               postgresql.UUID(),
                               sa.ForeignKey('authclient.id', ondelete='cascade'),
                               nullable=False)

    #: The authclient which created the authorization code.
    authclient = sa.orm.relationship('AuthClient')

    #: The authorization code itself
    code = sa.Column(sa.UnicodeText, nullable=False, unique=True)

    #: A timestamp after which this authorization code will no longer be
    #: considered valid.
    expires = sa.Column(sa.DateTime, nullable=False)
