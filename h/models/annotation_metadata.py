import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from h.db import Base


class AnnotationMetadata(Base):
    __tablename__ = "annotation_metadata"

    annotation_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("annotation_slim.id", ondelete="cascade"),
        nullable=False,
        primary_key=True,
    )
    """FK to annotation_slim.id"""

    annotation_slim = sa.orm.relationship("AnnotationSlim", back_populates="meta")

    data: Mapped[dict | None] = mapped_column(
        MutableDict.as_mutable(pg.JSONB()),
        default=dict,
        server_default=sa.func.jsonb("{}"),
    )
