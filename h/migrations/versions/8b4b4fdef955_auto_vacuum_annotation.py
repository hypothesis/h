"""Change auto-vacuum settings on big tables."""

from alembic import op

revision = "8b4b4fdef955"
down_revision = "0de98307b3c0"

BIG_TABLES = [
    "annotation",
    "annotation_slim",
    "annotation_metadata",
    "document",
    "user",
    "group",
]


def upgrade():
    for table in BIG_TABLES:
        # Set auto vacuum to kick in after 5% of dead tuples (vs total in the table) are detected
        op.execute(
            f'ALTER TABLE "{table}" SET (autovacuum_vacuum_scale_factor = 0.05);'
        )


def downgrade():
    # Set it back to the default value
    for table in BIG_TABLES:
        op.execute(
            f'ALTER TABLE "{table}" SET (autovacuum_vacuum_scale_factor = 0.20);'
        )
