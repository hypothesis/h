"""
Remove null document titles.

Revision ID: 5e535a075f16
Revises: a44ef07b085a
Create Date: 2016-09-14 15:11:26.551596
"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "5e535a075f16"
down_revision = "a44ef07b085a"


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
    n = 0
    for document_meta in session.query(DocumentMeta).filter_by(type="title"):
        new_titles = []
        for original_title in document_meta.value:
            if original_title is None:
                n += 1
                log.info(
                    "removing null title from document_meta {id}".format(
                        id=document_meta.id
                    )
                )
            else:
                new_titles.append(original_title)
        if len(new_titles) != len(document_meta.value):
            document_meta.value = new_titles
    session.commit()
    log.info("deleted {n} null document titles".format(n=n))


def downgrade():
    pass
