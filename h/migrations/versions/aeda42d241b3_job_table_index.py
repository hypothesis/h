"""Add index to the job table."""

from alembic import op

revision = "aeda42d241b3"
down_revision = "7bcd729defec"


def upgrade():
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")
    op.create_index(
        "ix__job_priority_enqueued_at",
        "job",
        ["priority", "enqueued_at"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index("ix__job_priority_enqueued_at", table_name="job")
