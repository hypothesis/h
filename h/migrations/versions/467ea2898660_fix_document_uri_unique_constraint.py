"""Fix document_uri unique constraint.

Revision ID: 467ea2898660
Revises: 296573bb30b3
Create Date: 2016-06-16 18:37:20.703447

"""

# revision identifiers, used by Alembic.
revision = '467ea2898660'
down_revision = '296573bb30b3'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from h.models import DocumentURI


Session = sessionmaker()


document_uri_table = sa.table('document_uri',
                              sa.column('type', sa.UnicodeText),
                              sa.column('content_type', sa.UnicodeText))


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
        session.query(DocumentURI.claimant_normalized,
                      DocumentURI.uri_normalized,
                      DocumentURI.type,
                      DocumentURI.content_type)
       .group_by(DocumentURI.claimant_normalized,
                 DocumentURI.uri_normalized,
                 DocumentURI.type,
                 DocumentURI.content_type)
        .having(sa.func.count('*') > 1))

    for group in groups:
        document_uris = (
            session.query(DocumentURI)
            .filter_by(claimant_normalized=group[0],
                       uri_normalized=group[1],
                       type=group[2],
                       content_type=group[3])
            .order_by(DocumentURI.updated.desc()))

        for document_uri in document_uris[1:]:
            session.delete(document_uri)


def change_nulls_to_empty_strings(db_session):
    """
    Change all null values in the type and content_type columns to ''.

    This will enable us to add NOT NULL constraints to the type and
    content_type columns with crashing.

    """
    db_session.execute(document_uri_table.update()\
        .where(document_uri_table.c.type == sa.sql.expression.null())\
        .values(type=''))
    db_session.execute(document_uri_table.update()\
        .where(document_uri_table.c.content_type == sa.sql.expression.null())\
        .values(content_type=''))


def upgrade():
    session = Session(bind=op.get_bind())
    merge_duplicate_document_uris(session)
    session.commit()
    change_nulls_to_empty_strings(session)
    session.commit()
    op.alter_column(
        'document_uri', 'type', nullable=False, server_default=u'')
    op.alter_column(
        'document_uri', 'content_type', nullable=False, server_default=u'')


def downgrade():
    op.alter_column('document_uri', 'type', nullable=True, server_default=None)
    op.alter_column(
        'document_uri', 'content_type', nullable=True, server_default=None)
