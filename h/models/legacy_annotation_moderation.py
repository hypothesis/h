import sqlalchemy as sa

from h.db import Base, types
from h.db.mixins import Timestamps


class _LegacyAnnotationModeration(Base, Timestamps):
    """
    A flag for a moderated and hidden annotation.

    This means that the annotation is violating the community guidelines and
    should be hidden from other users.

    This model/table is deprecated and replaced by Annoation.moderation_status column
    and the ModerationLog table.
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
            "_moderation",
            uselist=False,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    )

    def __repr__(self):
        return f"<_LegacyAnnotationModeration annotation_id={self.annotation_id}>"
