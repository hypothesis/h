"""Add version column to document_uri table."""

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "7c1a3e2b9f20"


def upgrade() -> None:
    op.add_column(
        "document_uri", sa.Column("version", sa.Integer(), nullable=True)
    )
    op.execute("COMMIT")
    op.execute("DROP INDEX CONCURRENTLY ix__document_uri_unique")
    op.execute(
        "CREATE UNIQUE INDEX CONCURRENTLY ix__document_uri_unique "
        "ON document_uri (md5(claimant_normalized), md5(uri_normalized), type, content_type, COALESCE(version, 0))"
    )


def downgrade() -> None:
    op.execute("COMMIT")
    op.execute("DROP INDEX CONCURRENTLY ix__document_uri_unique")
    op.execute(
        "CREATE UNIQUE INDEX CONCURRENTLY ix__document_uri_unique "
        "ON document_uri (md5(claimant_normalized), md5(uri_normalized), type, content_type)"
    )
    op.drop_column("document_uri", "version")
