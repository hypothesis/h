"""
Fix document_uri type fields.

Revision ID: 467ea2898660
Revises: 40740282ae9e
Create Date: 2016-06-16 18:37:20.703447
"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "467ea2898660"
down_revision = "40740282ae9e"


log = logging.getLogger(__name__)

Base = declarative_base()
Session = sessionmaker()


class DocumentURI(Base):
    __tablename__ = "document_uri"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    updated = sa.Column(sa.DateTime)

    claimant_normalized = sa.Column(sa.UnicodeText)
    uri_normalized = sa.Column(sa.UnicodeText)

    type = sa.Column(sa.UnicodeText)
    content_type = sa.Column(sa.UnicodeText)


def batch_delete(query, session):
    """
    Delete the result rows from the given query in batches.

    This minimizes the amount of time that the table(s) that the query selects
    from will be locked for at once.

    """
    n = 0
    query = query.limit(25)
    while True:
        if query.count() == 0:
            break
        for row in query:
            n += 1
            session.delete(row)
        session.commit()
    return n


def merge_duplicate_document_uris(session):
    """
    Merge duplicate document_uri rows into single rows.

    Find groups of document_uri rows that have the same claimant_normalized,
    uri_normalized, type and content_type.

    These duplicate rows must all contain null values in their type or
    content_type columns (or both) otherwise they couldn't co-exist in the
    database because of the
    (claimant_normalized, uri_normalized, type, content_type) unique
    constraint.

    These groups of duplicate rows will not be able to co-exist in the database
    anymore when we try to change null values in the type and content_type
    columns to empty strings in preparation for adding NOT NULL constraints to
    these columns.

    So for each group of duplicate rows delete all but the most recently
    updated row, thus enabling us to later change nulls to empty strings
    without crashing.

    """
    groups = (
        session.query(
            DocumentURI.claimant_normalized,
            DocumentURI.uri_normalized,
            DocumentURI.type,
            DocumentURI.content_type,
        )
        .group_by(
            DocumentURI.claimant_normalized,
            DocumentURI.uri_normalized,
            DocumentURI.type,
            DocumentURI.content_type,
        )
        .having(sa.func.count("*") > 1)
    )

    n = 0

    for group in groups:
        document_uris = (
            session.query(DocumentURI)
            .filter_by(
                claimant_normalized=group[0],
                uri_normalized=group[1],
                type=group[2],
                content_type=group[3],
            )
            .order_by(DocumentURI.updated.desc())
            .offset(1)
        )
        n += batch_delete(document_uris, session)

    log.info("deleted %d duplicate rows from document_uri (NULL)" % n)


def delete_conflicting_document_uris(session):
    """
    Delete NULL DocumentURIs where there's already an empty string one.

    Later we're going to be finding all DocumentURIs with NULL for their type
    or content_type and changing them to empty strings.  But for each one of
    these NULL DocumentURIs if there is already a matching DocumentURI - same
    claimant_normalized, uri_normalized, type and content_type but that already
    has an empty string instead of NULL for the type and/or content_type - then
    trying to change the NULL DocumentURI to an empty string one will fail with
    IntegrityError.

    So find all the DocumentURIs with an empty string for their type and/or
    content_type and for each one find any matching DocumentURIs but with
    NULL for the type and/or content_type and delete them.

    After this it should be safe to change all NULL types and content_types
    in document_uri to empty strings.

    """
    doc_uris = session.query(DocumentURI).filter(
        sa.or_(DocumentURI.type == "", DocumentURI.content_type == "")
    )

    n = 0

    for doc_uri in doc_uris:
        conflicting_doc_uris = session.query(DocumentURI).filter(
            DocumentURI.claimant_normalized == doc_uri.claimant_normalized,
            DocumentURI.uri_normalized == doc_uri.uri_normalized,
            DocumentURI.id != doc_uri.id,
        )

        if doc_uri.type == "" and doc_uri.content_type == "":
            conflicting_doc_uris = conflicting_doc_uris.filter(
                sa.or_(DocumentURI.type == "", DocumentURI.type.is_(None)),
                sa.or_(
                    DocumentURI.content_type == "", DocumentURI.content_type.is_(None)
                ),
            )
        elif doc_uri.type == "":
            conflicting_doc_uris = conflicting_doc_uris.filter(
                sa.or_(DocumentURI.type == "", DocumentURI.type.is_(None)),
                DocumentURI.content_type == doc_uri.content_type,
            )
        elif doc_uri.content_type == "":
            conflicting_doc_uris = conflicting_doc_uris.filter(
                DocumentURI.type == doc_uri.type,
                sa.or_(
                    DocumentURI.content_type == "", DocumentURI.content_type.is_(None)
                ),
            )

        n += batch_delete(conflicting_doc_uris, session)

    log.info("deleted %d duplicate rows from document_uri (empty string/NULL)" % n)


def change_nulls_to_empty_strings(session):
    """
    Change all null values in the type and content_type columns to ''.

    This will enable us to add NOT NULL constraints to the type and
    content_type columns with crashing.

    """
    n = 0

    while True:
        doc_uris = (
            session.query(DocumentURI)
            .filter(
                sa.or_(
                    DocumentURI.type == sa.sql.expression.null(),
                    DocumentURI.content_type == sa.sql.expression.null(),
                )
            )
            .limit(25)
        )

        if doc_uris.count() == 0:
            break

        for doc_uri in doc_uris:
            n += 1
            doc_uri.type = doc_uri.type or ""
            doc_uri.content_type = doc_uri.content_type or ""

        session.commit()

    log.info("replaced NULL with '' in %d rows" % n)


def upgrade():
    session = Session(bind=op.get_bind())
    merge_duplicate_document_uris(session)
    delete_conflicting_document_uris(session)
    change_nulls_to_empty_strings(session)


def downgrade():
    pass
