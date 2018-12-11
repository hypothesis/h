"""Add Document URI and Meta document_id index

Revision ID: 77c2af032aca
Revises: f3b8e76ae9f5
Create Date: 2016-05-13 15:06:55.496502

"""

# revision identifiers, used by Alembic.
revision = "77c2af032aca"
down_revision = "f3b8e76ae9f5"

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__document_uri_document_id"),
        "document_uri",
        ["document_id"],
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__document_meta_document_id"),
        "document_meta",
        ["document_id"],
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__document_uri_document_id"), "document_uri")
    op.drop_index(op.f("ix__document_meta_document_id"), "document_meta")
