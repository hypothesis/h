"""
Clean up moderation extra key

Revision ID: b102c50b1133
Revises: 50df3e6782aa
Create Date: 2017-04-10 14:58:14.472500
"""

from __future__ import unicode_literals

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import sessionmaker

from h.db import types

revision = "b102c50b1133"
down_revision = "50df3e6782aa"

Base = declarative_base()
Session = sessionmaker()

log = logging.getLogger(__name__)


class Annotation(Base):
    __tablename__ = "annotation"
    id = sa.Column(types.URLSafeUUID, primary_key=True)
    extra = sa.Column(
        MutableDict.as_mutable(pg.JSONB),
        default=dict,
        server_default=sa.func.jsonb("{}"),
        nullable=False,
    )


def upgrade():
    session = Session(bind=op.get_bind())

    anns = session.query(Annotation).filter(Annotation.extra.has_key("moderation"))
    found = 0
    for ann in anns:
        del ann.extra["moderation"]
        found += 1

    log.info(
        "Found and cleaned up %d annotations with a moderation key in the extras field",
        found,
    )
    session.commit()


def downgrade():
    pass
