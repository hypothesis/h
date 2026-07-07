from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from h.db import Base
from h.db.mixins import Timestamps
from h.models import helpers


class Checkpoint(Base, Timestamps):
    """A hide/reveal checkpoint, synced from the LMS so h can authorize annotation visibility.

    Checkpoints form a per-(group, document) linked list: a checkpoint's start
    date is derived from its predecessor's reveal_date, and the first one
    (previous_checkpoint_id NULL) starts at the assignment creation date.
    Annotations stay hidden until their checkpoint's reveal_date passes.
    """

    __tablename__ = "checkpoint"

    id: Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)

    group_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("group.id", ondelete="CASCADE"), nullable=False
    )
    group = sa.orm.relationship("Group")

    document_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    document = sa.orm.relationship("Document")

    previous_checkpoint_id: Mapped[int | None] = mapped_column(
        sa.Integer, sa.ForeignKey("checkpoint.id", ondelete="CASCADE"), nullable=True
    )
    previous_checkpoint = sa.orm.relationship(
        "Checkpoint", remote_side=[id], uselist=False
    )

    reveal_date: Mapped[datetime | None] = mapped_column(sa.DateTime, nullable=True)
    """When the instructor reveals this checkpoint; NULL until revealed."""

    __table_args__ = (
        # NULLS NOT DISTINCT (PG15+) so the NULL-previous root is unique too:
        # at most one first checkpoint per (group, uri).
        sa.UniqueConstraint(
            "group_id",
            "document_id",
            "previous_checkpoint_id",
            name="uq__checkpoint__group_id__document_id__previous_checkpoint_id",
            postgresql_nulls_not_distinct=True,
        ),
    )

    def __repr__(self) -> str:
        return helpers.repr_(
            self, ["id", "group_id", "previous_checkpoint_id", "reveal_date"]
        )
