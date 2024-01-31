"""
Remove whitespace from the document_uri.uri column.

Revision ID: 63e8b1fe1d4b
Revises: 6d9257ad610d
Create Date: 2016-09-15 15:26:31.286536
"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "63e8b1fe1d4b"
down_revision = "53a74d7ae1b0"

log = logging.getLogger(__name__)


Base = declarative_base()
Session = sessionmaker()


class DocumentURI(Base):
    __tablename__ = "document_uri"
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    uri = sa.Column(sa.UnicodeText)


def upgrade():
    session = Session(bind=op.get_bind())
    changed = []
    to_delete = []
    for document_uri in session.query(DocumentURI):
        stripped_uri = document_uri.uri.strip()
        if not stripped_uri:
            to_delete.append(document_uri)
        elif stripped_uri != document_uri.uri:
            document_uri.uri = stripped_uri
            changed.append(document_uri)

    for document_uri in to_delete:
        session.delete(document_uri)

    session.commit()

    log.info("Removed whitespace from {n} document_uris".format(n=len(changed)))
    log.info("Deleted {n} document_uris with empty uris".format(n=len(to_delete)))


def downgrade():
    pass
