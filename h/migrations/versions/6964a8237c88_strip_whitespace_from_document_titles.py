"""
Strip whitespace from document titles.

Revision ID: 6964a8237c88
Revises: 5e535a075f16
Create Date: 2016-09-14 15:17:23.096224
"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "6964a8237c88"
down_revision = "5e535a075f16"


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
            stripped_title = original_title.strip()
            if original_title != stripped_title:
                n += 1
                log.info(
                    "updated '{original_title}' to '{stripped_title}'".format(
                        original_title=original_title, stripped_title=stripped_title
                    )
                )
            new_titles.append(stripped_title)

        if new_titles != document_meta.value:
            document_meta.value = new_titles

    session.commit()
    log.info("updated {n} document titles".format(n=n))


def downgrade():
    pass
