"""
Remove trailing # from PDF URNs.

Revision ID: 9e6b4f70f588
Revises: 467ea2898660
Create Date: 2016-06-21 17:50:14.261947

"""

# pylint: disable=invalid-name, wrong-import-position
import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from h.db import types

# revision identifiers, used by Alembic.
revision = "9e6b4f70f588"
down_revision = "ccebe818f8e0"


Base = declarative_base()
Session = sessionmaker()


log = logging.getLogger(__name__)


class Annotation(Base):
    __tablename__ = "annotation"
    id = sa.Column(types.URLSafeUUID, primary_key=True)
    target_uri = sa.Column(sa.UnicodeText)


class DocumentURI(Base):
    __tablename__ = "document_uri"
    id = sa.Column(sa.Integer, primary_key=True)
    claimant = sa.Column(sa.UnicodeText)
    claimant_normalized = sa.Column(sa.UnicodeText)
    uri = sa.Column(sa.UnicodeText)
    uri_normalized = sa.Column(sa.UnicodeText)
    type = sa.Column(sa.UnicodeText)
    content_type = sa.Column(sa.UnicodeText)


def upgrade():
    session = Session(bind=op.get_bind())

    document_uris = session.query(DocumentURI).filter(
        sa.or_(
            DocumentURI.claimant.like("urn:x-pdf:%#"),
            DocumentURI.claimant_normalized.like("urn:x-pdf:%#"),
            DocumentURI.uri.like("urn:x-pdf:%#"),
            DocumentURI.uri_normalized.like("urn:x-pdf:%#"),
        )
    )

    num_doc_uris_with_trailing_hashes = 0
    num_conflicting_doc_uris = 0
    num_without_conflicting_doc_uris = 0

    for doc_uri in document_uris:
        any_trailing_hash_found = False

        if doc_uri.claimant.endswith("#"):
            any_trailing_hash_found = True
            new_claimant = doc_uri.claimant[:-1]
        else:
            new_claimant = doc_uri.claimant

        if doc_uri.claimant_normalized.endswith("#"):
            any_trailing_hash_found = True
            new_claimant_normalized = doc_uri.claimant_normalized[:-1]
        else:
            new_claimant_normalized = doc_uri.claimant_normalized

        if doc_uri.uri.endswith("#"):
            any_trailing_hash_found = True
            new_uri = doc_uri.uri[:-1]
        else:
            new_uri = doc_uri.uri

        if doc_uri.uri_normalized.endswith("#"):
            any_trailing_hash_found = True
            new_uri_normalized = doc_uri.uri_normalized[:-1]
        else:
            new_uri_normalized = doc_uri.uri_normalized

        if any_trailing_hash_found:
            num_doc_uris_with_trailing_hashes += 1

        conflicting_doc_uris = session.query(DocumentURI).filter_by(
            claimant_normalized=new_claimant_normalized,
            uri_normalized=new_uri_normalized,
            type=doc_uri.type,
            content_type=doc_uri.content_type,
        )

        conflicting_doc_uri = conflicting_doc_uris.one_or_none()

        if conflicting_doc_uri:
            num_conflicting_doc_uris += 1
            session.delete(doc_uri)
        else:
            num_without_conflicting_doc_uris += 1
            doc_uri.claimant = new_claimant
            doc_uri.claimant_normalized = new_claimant_normalized
            doc_uri.uri = new_uri
            doc_uri.uri_normalized = new_uri_normalized

    log.info("found %s rows with trailing #'s", num_doc_uris_with_trailing_hashes)
    log.info(
        "%s of these were deleted because rows without the trailing "
        "#'s already existed",
        num_conflicting_doc_uris,
    )
    log.info(
        "and %s rows were updated to remove trailing #'s",
        num_without_conflicting_doc_uris,
    )

    annotations = session.query(Annotation).filter(
        Annotation.target_uri.like("urn:x-pdf:%#")
    )

    log.info(
        "removing trailing #'s from target_uri's of %s annotations", annotations.count()
    )

    for annotation in annotations:
        annotation.target_uri = annotation.target_uri[:-1]

    session.commit()


def downgrade():
    pass
