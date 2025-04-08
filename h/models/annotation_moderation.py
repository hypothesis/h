from h.db.mixins_dataclasses import AutoincrementingIntegerID
import sqlalchemy as sa

from h.db import Base, types
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    relationship,
    mapped_column,
)
from h.db.mixins import CreatedMixin, Timestamps
from sqlalchemy import ForeignKey


class ModerationLog(Base, AutoincrementingIntegerID, CreatedMixin, MappedAsDataclass):
    __tablename__ = "moderation_log"

    user_id: Mapped[int] = mapped_column(sa.ForeignKey("user.id", ondelete="CASCADE"))
    user = relationship("User")

    annotation_id: Mapped[types.URLSafeUUID] = mapped_column(
        ForeignKey("annotation.id", ondelete="CASCADE"), index=True
    )

    old_moderation_status: Mapped[str] = mapped_column()
    new_moderation_status: Mapped[str] = mapped_column()


class AnnotationModeration(Base, Timestamps):
    """
    A flag for a moderated and hidden annotation.

    This means that the annotation is violating the community guidelines and
    should be hidden from other users.
    """

    __tablename__ = "annotation_moderation"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    annotation_id = sa.Column(
        types.URLSafeUUID,
        sa.ForeignKey("annotation.id", ondelete="cascade"),
        nullable=False,
        unique=True,
    )

    #: The annotation which has been flagged.
    annotation = sa.orm.relationship(
        "Annotation",
        backref=sa.orm.backref(
            "moderation",
            uselist=False,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    )

    def __repr__(self):
        return f"<AnnotationModeration annotation_id={self.annotation_id}>"
