"""Fix document_uri unique constraint.

Revision ID: 467ea2898660
Revises: 296573bb30b3
Create Date: 2016-06-16 18:37:20.703447

"""

# revision identifiers, used by Alembic.
revision = '467ea2898660'
down_revision = '296573bb30b3'

from alembic import op
from sqlalchemy.orm import sessionmaker

from h.fix_document_uri_unique_constraint import merge_duplicate_document_uris, change_nulls_to_empty_strings


Session = sessionmaker()


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
