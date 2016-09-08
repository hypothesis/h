# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from h.db import Base
from h.db.mixins import Timestamps
from h.security import token_urlsafe


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

    #: Public client identifier
    id = sa.Column(postgresql.UUID,
                   server_default=sa.func.uuid_generate_v1mc(),
                   primary_key=True)

    #: Human-readable name for reference.
    name = sa.Column(sa.UnicodeText, nullable=True)

    #: Client secret
    secret = sa.Column(sa.UnicodeText, default=token_urlsafe, nullable=False)

    #: Authority for which this client is allowed to authorize users.
    authority = sa.Column(sa.UnicodeText, nullable=False)

    def __repr__(self):
        return 'AuthClient(id={self.id!r})'.format(self=self)
