"""Add task done table.

Revision ID: 9d97a3e4921e
Revises: 372308320143
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "9d97a3e4921e"
down_revision = "372308320143"


def upgrade() -> None:
    op.create_table(
        "task_done",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(),
            server_default=sa.text("now() + interval '30 days'"),
            nullable=False,
        ),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__task_done")),
    )


def downgrade() -> None:
    op.drop_table("task_done")
