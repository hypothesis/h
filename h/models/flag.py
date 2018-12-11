# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa

from h.db import Base, types
from h.db.mixins import Timestamps


class Flag(Base, Timestamps):
    """
    A flag representing a user request for moderator attention.

    Users can "flag" annotations if they believe that the annotation in question violates the
    content policy of the group or service, or otherwise needs moderator attention.
    """

    __tablename__ = "flag"
    __table_args__ = (sa.UniqueConstraint("annotation_id", "user_id"),)

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    annotation_id = sa.Column(
        types.URLSafeUUID,
        sa.ForeignKey("annotation.id", ondelete="cascade"),
        nullable=False,
    )

    #: The annotation which has been flagged.
    annotation = sa.orm.relationship("Annotation")

    user_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("user.id", ondelete="cascade"),
        nullable=False,
        index=True,
    )

    #: The user who created the flag.
    user = sa.orm.relationship("User")

    def __repr__(self):
        return "<Flag annotation_id=%s user_id=%s>" % (self.annotation_id, self.user_id)
