from h.db import Base, types
from sqlalchemy.dialects import postgresql as pg
import sqlalchemy as sa
from sqlalchemy.ext.mutable import MutableDict


class AnnotationMetadata(Base):
    __tablename__ = "annotation_metadata"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    annotation_pk = sa.Column(
        sa.Integer,
        sa.ForeignKey("annotation.pk", ondelete="cascade"),
        nullable=False,
        unique=True,
    )

    lms = sa.Column(
        MutableDict.as_mutable(pg.JSONB),
        default=dict,
        server_default=sa.func.jsonb("{}"),
        nullable=True,
    )
