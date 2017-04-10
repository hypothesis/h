"""
Fill in missing denormalized Document.web_uri

Revision ID: a44ef07b085a
Revises: 58bb601c390f
Create Date: 2016-09-12 15:31:00.597582
"""

from __future__ import unicode_literals

from collections import namedtuple

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import subqueryload

from h._compat import urlparse


revision = 'a44ef07b085a'
down_revision = '58bb601c390f'

Base = declarative_base()
Session = sessionmaker()


class Window(namedtuple('Window', ['start', 'end'])):
    pass


class Document(Base):
    __tablename__ = 'document'
    id = sa.Column(sa.Integer, primary_key=True)
    updated = sa.Column(sa.DateTime)
    web_uri = sa.Column(sa.UnicodeText())
    document_uris = sa.orm.relationship('DocumentURI',
                                        backref='document',
                                        order_by='DocumentURI.created.asc()')


class DocumentURI(Base):
    __tablename__ = 'document_uri'
    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime)
    uri = sa.Column(sa.UnicodeText)
    document_id = sa.Column(sa.Integer,
                            sa.ForeignKey('document.id'),
                            nullable=False)


def upgrade():
    session = Session(bind=op.get_bind())

    windows = _fetch_windows(session)
    session.rollback()

    for window in windows:
        query = session.query(Document) \
            .filter(Document.updated.between(window.start, window.end)) \
            .options(subqueryload(Document.document_uris)) \
            .order_by(Document.updated.asc())

        for doc in query:
            doc.web_uri = _document_web_uri(doc)

        session.commit()


def downgrade():
    pass


def _document_web_uri(document):
    for docuri in document.document_uris:
        uri = urlparse.urlparse(docuri.uri)
        if uri.scheme in ['http', 'https']:
            return docuri.uri


def _fetch_windows(session, chunksize=100):
    updated = session.query(Document.updated). \
        execution_options(stream_results=True). \
        order_by(Document.updated.desc()).all()

    count = len(updated)
    windows = [Window(start=updated[min(x+chunksize, count)-1].updated,
                      end=updated[x].updated)
               for x in xrange(0, count, chunksize)]

    return windows
