from enum import StrEnum

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from h.db import Base, types
from h.db.mixins import Timestamps
from h.models import helpers


class NotificationType(StrEnum):
    MENTION = "mention"
    REPLY = "reply"


class EmailTag(StrEnum):
    ACTIVATION = "activation"
    FLAG_NOTIFICATION = "flag_notification"
    REPLY_NOTIFICATION = "reply_notification"
    RESET_PASSWORD = "reset_password"  # noqa: S105
    MENTION_NOTIFICATION = "mention_notification"
    TEST = "test"


class Notification(Base, Timestamps):  # pragma: no cover
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    source_annotation_id: Mapped[types.URLSafeUUID] = mapped_column(
        ForeignKey("annotation.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """FK to annotation.id - the annotation that triggered this notification"""
    source_annotation = relationship(
        "Annotation", back_populates="notifications", uselist=False
    )

    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """FK to user.id - the user receiving the notification"""
    recipient = relationship("User", uselist=False)

    notification_type: Mapped[NotificationType]
    """Type of notification (mention, reply, etc.)"""

    __table_args__ = (
        # Ensure that a recipient can only have one notification for a given source annotation
        UniqueConstraint(
            "recipient_id",
            "source_annotation_id",
            name="uq__notification__recipient_id__source_annotation_id",
        ),
    )

    def __repr__(self) -> str:
        return helpers.repr_(self, ["id", "source_annotation_id"])
