"""Add missing unique constraint on annotation_medatada."""

import sqlalchemy as sa
from alembic import op

revision = "78d3d6fe1d42"
down_revision = "a122e276f8d1"


def upgrade():
    conn = op.get_bind()

    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT;")

    # First create the index concurrently to avoid locking the table
    conn.execute(
        sa.text(
            """
        CREATE UNIQUE INDEX CONCURRENTLY ix__annotation_metadata__annotation_id ON annotation_metadata (annotation_id);
    """
        )
    )
    # Once the index is created, use it to create the unique constraint
    conn.execute(
        sa.text(
            """
            ALTER TABLE annotation_metadata ADD CONSTRAINT uq__annotation_metadata__annotation_id UNIQUE USING INDEX ix__annotation_metadata__annotation_id
    """
        )
    )


def downgrade():
    op.drop_constraint(
        op.f("uq__annotation_metadata__annotation_id"),
        "annotation_metadata",
        type_="unique",
    )
