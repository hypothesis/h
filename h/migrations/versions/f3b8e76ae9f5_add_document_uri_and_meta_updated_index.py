"""
Add Document URI and Meta updated index.

Revision ID: f3b8e76ae9f5
Revises: fde6cdcdd39a
Create Date: 2016-05-13 14:58:37.679724

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f3b8e76ae9f5"
down_revision = "fde6cdcdd39a"


def upgrade():
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__document_uri_updated"),
        "document_uri",
        ["updated"],
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__document_meta_updated"),
        "document_meta",
        ["updated"],
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__document_uri_updated"), "document_uri")
    op.drop_index(op.f("ix__document_meta_updated"), "document_meta")
