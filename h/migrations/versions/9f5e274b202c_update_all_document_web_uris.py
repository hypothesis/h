"""
Update all Document.web_uris.

Revision ID: 9f5e274b202c
Revises: e10ce4472966
Create Date: 2017-01-20 16:07:03.442975
"""

from __future__ import unicode_literals

from collections import namedtuple
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import subqueryload

from h._compat import urlparse


revision = '9f5e274b202c'
down_revision = 'e10ce4472966'


Base = declarative_base()
Session = sessionmaker()
log = logging.getLogger(__name__)


class Window(namedtuple('Window', ['start', 'end'])):
    pass


class Document(Base):
    __tablename__ = 'document'
    id = sa.Column(sa.Integer, primary_key=True)
    updated = sa.Column(sa.DateTime)
    web_uri = sa.Column(sa.UnicodeText())
    document_uris = sa.orm.relationship('DocumentURI',
                                        backref='document',
                                        order_by='DocumentURI.updated.desc()')

    def updated_web_uri(self):
        def first_http_url(type_=None):
            for document_uri in self.document_uris:
                uri = document_uri.uri
                if type_ is not None and document_uri.type != type_:
                    continue
                if urlparse.urlparse(uri).scheme not in ['http', 'https']:
                    continue
                return document_uri.uri

        return (first_http_url(type_='self-claim') or
                first_http_url(type_='rel-canonical') or
                first_http_url())


class DocumentURI(Base):
    __tablename__ = 'document_uri'
    id = sa.Column(sa.Integer, primary_key=True)
    updated = sa.Column(sa.DateTime)
    uri = sa.Column(sa.UnicodeText)
    type = sa.Column(sa.UnicodeText,
                     nullable=False,
                     default='',
                     server_default='')
    document_id = sa.Column(sa.Integer,
                            sa.ForeignKey('document.id'),
                            nullable=False)


def upgrade():
    session = Session(bind=op.get_bind())

    windows = _fetch_windows(session)
    session.rollback()

    updated = 0
    not_changed = 0
    for window in windows:
        query = session.query(Document) \
            .filter(Document.updated.between(window.start, window.end)) \
            .options(subqueryload(Document.document_uris)) \
            .order_by(Document.updated.asc())

        for doc in query:
            updated_web_uri = doc.updated_web_uri()
            if updated_web_uri and updated_web_uri != doc.web_uri:
                doc.web_uri = updated_web_uri
                updated += 1
            else:
                not_changed += 1

        session.commit()

    log.info("Updated {updated} web_uris".format(updated=updated))
    log.info("Left {not_changed} web_uris unchanged".format(not_changed=not_changed))


def downgrade():
    pass


def _fetch_windows(session, chunksize=100):
    updated = session.query(Document.updated). \
        execution_options(stream_results=True). \
        order_by(Document.updated.desc()).all()

    count = len(updated)
    windows = [Window(start=updated[min(x+chunksize, count)-1].updated,
                      end=updated[x].updated)
               for x in xrange(0, count, chunksize)]

    return windows
