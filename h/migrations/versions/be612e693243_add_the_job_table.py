"""Add the job table."""
from alembic import op
from sqlalchemy import Column, DateTime, Integer, Sequence, UnicodeText, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import CreateSequence, DropSequence

revision = "be612e693243"
down_revision = "64039842150a"


def upgrade():
    op.execute(CreateSequence(Sequence("job_id_seq", cycle=True)))
    op.create_table(
        "job",
        Column("id", Integer, Sequence("job_id_seq", cycle=True), primary_key=True),
        Column("name", UnicodeText, nullable=False),
        Column("enqueued_at", DateTime, nullable=False, server_default=func.now()),
        Column("scheduled_at", DateTime, nullable=False, server_default=func.now()),
        Column(
            "expires_at",
            DateTime,
            nullable=False,
            server_default=text("now() + interval '30 days'"),
        ),
        Column("priority", Integer, nullable=False),
        Column("tag", UnicodeText, nullable=False),
        Column(
            "kwargs",
            JSONB,
            server_default=text("'{}'::jsonb"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_table("job")
    op.execute(DropSequence(Sequence("job_id_seq")))
