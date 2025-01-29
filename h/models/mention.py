import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from h.db import Base
from h.db.mixins import Timestamps
from h.models import helpers


class Mention(Base, Timestamps):  # pragma: nocover
    __tablename__ = "mention"

    id: Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)

    annotation_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey("annotation_slim.id", ondelete="CASCADE"),
        nullable=False,
    )
    """FK to annotation_slim.id"""
    annotation = sa.orm.relationship("AnnotationSlim", back_populates="mentions")

    user_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """FK to user.id"""
    user = sa.orm.relationship("User")

    def __repr__(self) -> str:
        return helpers.repr_(self, ["id", "annotation_id", "user_id"])
