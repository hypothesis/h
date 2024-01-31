"""
Delete document_meta rows that have type 'title' and an empty array value.

Revision ID: 6d9257ad610d
Revises: 3d71ec81d18c
Create Date: 2016-09-14 16:06:33.439592
"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "6d9257ad610d"
down_revision = "3d71ec81d18c"


log = logging.getLogger(__name__)


Base = declarative_base()
Session = sessionmaker()


class DocumentMeta(Base):
    __tablename__ = "document_meta"
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    type = sa.Column(sa.UnicodeText)
    value = sa.Column(pg.ARRAY(sa.UnicodeText, zero_indexes=True))


def upgrade():
    session = Session(bind=op.get_bind())
    to_delete = []
    for document_meta in session.query(DocumentMeta).filter_by(type="title"):
        if document_meta.value == []:
            to_delete.append(document_meta)
    for document_meta in to_delete:
        session.delete(document_meta)
    session.commit()
    log.info("deleted {n} empty-array document titles".format(n=len(to_delete)))


def downgrade():
    pass
