"""
Fill in missing denormalized Document.title

Revision ID: 58bb601c390f
Revises: 3e1727613916
Create Date: 2016-09-12 12:21:40.904620
"""

from __future__ import unicode_literals

from collections import namedtuple

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import subqueryload


revision = "58bb601c390f"
down_revision = "3e1727613916"

Base = declarative_base()
Session = sessionmaker()


class Window(namedtuple("Window", ["start", "end"])):
    pass


class Document(Base):
    __tablename__ = "document"
    id = sa.Column(sa.Integer, primary_key=True)
    updated = sa.Column(sa.DateTime)
    title = sa.Column(sa.UnicodeText())
    meta_titles = sa.orm.relationship(
        "DocumentMeta",
        primaryjoin='and_(Document.id==DocumentMeta.document_id, DocumentMeta.type==u"title")',
        order_by="DocumentMeta.updated.asc()",
        viewonly=True,
    )


class DocumentMeta(Base):
    __tablename__ = "document_meta"
    id = sa.Column(sa.Integer, primary_key=True)
    updated = sa.Column(sa.DateTime)
    type = sa.Column(sa.UnicodeText)
    value = sa.Column(sa.UnicodeText)
    document_id = sa.Column(sa.Integer, sa.ForeignKey("document.id"), nullable=False)


def upgrade():
    session = Session(bind=op.get_bind())

    windows = _fetch_windows(session)
    session.rollback()

    for window in windows:
        query = (
            session.query(Document)
            .filter(Document.updated.between(window.start, window.end))
            .options(subqueryload(Document.meta_titles))
            .order_by(Document.updated.asc())
        )

        for doc in query:
            doc.title = _document_title(doc)

        session.commit()


def downgrade():
    pass


def _document_title(document):
    for meta in document.meta_titles:
        if meta.value:
            return meta.value[0]


def _fetch_windows(session, chunksize=100):
    updated = (
        session.query(Document.updated)
        .execution_options(stream_results=True)
        .order_by(Document.updated.desc())
        .all()
    )

    count = len(updated)
    windows = [
        Window(
            start=updated[min(x + chunksize, count) - 1].updated, end=updated[x].updated
        )
        for x in xrange(0, count, chunksize)
    ]

    return windows
