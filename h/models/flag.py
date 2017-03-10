# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa

from memex.db import types

from h.db import Base
from h.db.mixins import Timestamps


class Flag(Base, Timestamps):
    """
    A flag.

    A user can flag up content, in this case just annotations,
    which are then being moderated by group moderators.
    """

    __tablename__ = 'flag'
    __table_args__ = (sa.UniqueConstraint('annotation_id', 'user_id'),)

    #: The id of the flag.
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    annotation_id = sa.Column(types.URLSafeUUID,
                              sa.ForeignKey('annotation.id', ondelete='cascade'),
                              nullable=False)

    #: The annotation which has been flagged.
    annotation = sa.orm.relationship('Annotation')

    user_id = sa.Column(sa.Integer,
                        sa.ForeignKey('user.id', ondelete='cascade'),
                        nullable=False)

    #: The user who created the flag.
    user = sa.orm.relationship('User')

    def __repr__(self):
        return '<Flag annotation_id=%s user_id=%s>' % (self.annotation_id,
                                                       self.user_id)
