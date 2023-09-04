"""Create index on annotation.created."""
from alembic import op

revision = "95825c951c08"
down_revision = "7d39ade34b69"


def upgrade():
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")
    op.execute(
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS ix__annotation_created ON "annotation" (created);"""
    )


def downgrade():
    op.drop_index("ix__annotation_created", table_name="annotation")
