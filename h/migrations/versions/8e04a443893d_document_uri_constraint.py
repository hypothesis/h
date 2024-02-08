"""Unique document uri index with hash function."""

from alembic import op

revision = "8e04a443893d"
down_revision = "8f5b6f8bbba8"


def upgrade():
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")
    # Create index for the constraint first, concurrently
    op.execute(
        """CREATE UNIQUE INDEX CONCURRENTLY ix__document_uri_unique ON document_uri (md5(claimant_normalized), md5(uri_normalized), type, content_type);"""
    )


def downgrade():
    op.execute("DROP INDEX ix__document_uri_unique")
