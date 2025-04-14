from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)

from h.db import Base, types
from h.db.mixins_dataclasses import AutoincrementingIntegerID, CreatedMixin
from h.models.annotation import ModerationStatus


class ModerationLog(Base, AutoincrementingIntegerID, CreatedMixin, MappedAsDataclass):
    __tablename__ = "moderation_log"

    moderator_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    moderator = relationship("User")

    annotation_id: Mapped[types.URLSafeUUID] = mapped_column(
        ForeignKey("annotation.id", ondelete="CASCADE"), index=True
    )
    annotation = relationship("Annotation")

    old_moderation_status: Mapped[ModerationStatus | None] = mapped_column()
    new_moderation_status: Mapped[ModerationStatus] = mapped_column()
