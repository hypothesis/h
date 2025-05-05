from typing import TYPE_CHECKING, Optional

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

if TYPE_CHECKING:
    from h.models import Annotation, User


class ModerationLog(Base, AutoincrementingIntegerID, CreatedMixin, MappedAsDataclass):
    __tablename__ = "moderation_log"

    moderator: Mapped[Optional["User"]] = relationship("User")
    annotation: Mapped["Annotation"] = relationship("Annotation")

    old_moderation_status: Mapped[ModerationStatus | None] = mapped_column()
    new_moderation_status: Mapped[ModerationStatus] = mapped_column()

    moderator_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), default=None
    )
    annotation_id: Mapped[types.URLSafeUUID] = mapped_column(
        ForeignKey("annotation.id", ondelete="CASCADE"), index=True, default=None
    )
