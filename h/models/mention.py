import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from h.db import Base, types
from h.db.mixins import Timestamps
from h.models import helpers


class Mention(Base, Timestamps):  # pragma: nocover
    __tablename__ = "mention"

    id: Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)

    annotation_id: Mapped[types.URLSafeUUID] = mapped_column(
        types.URLSafeUUID,
        sa.ForeignKey("annotation.id", ondelete="CASCADE"),
        nullable=False,
    )
    """FK to annotation.id"""
    annotation = sa.orm.relationship("Annotation", back_populates="mentions")

    user_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """FK to user.id"""
    user = sa.orm.relationship("User")

    username: Mapped[str] = mapped_column(sa.UnicodeText, nullable=False)
    """The username of the mentioned user at the time of the mention"""

    def __repr__(self) -> str:
        return helpers.repr_(self, ["id", "annotation_id", "user_id"])
