"""
Fill in missing Annotation.document_id

Revision ID: bcdd81e23920
Revises: addee5d1686f
Create Date: 2016-09-22 16:02:42.284670
"""

from __future__ import unicode_literals

from collections import namedtuple
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import subqueryload

from h.db import types
from h.util.uri import normalize as uri_normalize


revision = "bcdd81e23920"
down_revision = "addee5d1686f"

log = logging.getLogger(__name__)

Base = declarative_base()
Session = sessionmaker()


class Window(namedtuple("Window", ["start", "end"])):
    pass


class Document(Base):
    __tablename__ = "document"
    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime)
    updated = sa.Column(sa.DateTime)
    web_uri = sa.Column("web_uri", sa.UnicodeText())
    document_uris = sa.orm.relationship(
        "DocumentURI", backref="document", order_by="DocumentURI.created.asc()"
    )


class DocumentURI(Base):
    __tablename__ = "document_uri"
    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime)
    updated = sa.Column(sa.DateTime)
    uri = sa.Column(sa.UnicodeText)
    uri_normalized = sa.Column(sa.UnicodeText)
    claimant = sa.Column(sa.UnicodeText)
    claimant_normalized = sa.Column(sa.UnicodeText)
    type = sa.Column(sa.UnicodeText)
    document_id = sa.Column(sa.Integer, sa.ForeignKey("document.id"), nullable=False)


class Annotation(Base):
    __tablename__ = "annotation"
    id = sa.Column(types.URLSafeUUID, primary_key=True)
    created = sa.Column(sa.DateTime)
    updated = sa.Column(sa.DateTime)
    target_uri = sa.Column(sa.UnicodeText)
    target_uri_normalized = sa.Column(sa.UnicodeText)
    document_id = sa.Column(sa.Integer, sa.ForeignKey("document.id"), nullable=True)
    document = sa.orm.relationship("Document")
    document_through_uri = sa.orm.relationship(
        "Document",
        secondary="document_uri",
        primaryjoin="Annotation.target_uri_normalized == DocumentURI.uri_normalized",
        secondaryjoin="DocumentURI.document_id == Document.id",
        viewonly=True,
        uselist=False,
    )


def upgrade():
    session = Session(bind=op.get_bind())

    windows = _fetch_windows(session)
    session.rollback()

    new_documents = 0
    document_id_updated = 0

    for window in windows:
        query = (
            session.query(Annotation)
            .filter(Annotation.updated.between(window.start, window.end))
            .filter(Annotation.document_id.is_(None))
            .order_by(Annotation.updated.asc())
        )

        for ann in query:
            if ann.document_id:
                continue

            if ann.document_through_uri is None:
                uri = ann.target_uri
                uri_normalized = uri_normalize(uri)

                doc = Document(created=ann.created, updated=ann.updated)
                docuri = DocumentURI(
                    created=ann.created,
                    updated=ann.updated,
                    claimant=uri,
                    claimant_normalized=uri_normalized,
                    uri=uri,
                    uri_normalized=uri_normalized,
                    type="self-claim",
                    document=doc,
                )
                ann.document = doc
                session.flush()
                new_documents += 1
            else:
                ann.document_id = ann.document_through_uri.id
                document_id_updated += 1

        session.commit()

    log.debug("Created %d new documents" % new_documents)
    log.debug("Filled in %d existing document ids" % document_id_updated)


def downgrade():
    pass


def _fetch_windows(session, chunksize=200):
    updated = (
        session.query(Annotation.updated)
        .filter_by(document_id=None)
        .execution_options(stream_results=True)
        .order_by(Annotation.updated.desc())
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
