"""Create the checkpoint table."""

import sqlalchemy as sa
from alembic import op

revision = "3794945d8e88"
down_revision = "a1b2c3d4e5f6"


def upgrade() -> None:
    op.create_table(
        "checkpoint",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("document_uri", sa.UnicodeText(), nullable=False),
        sa.Column("previous_checkpoint_id", sa.Integer(), nullable=True),
        sa.Column("reveal_date", sa.DateTime(), nullable=True),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__checkpoint__group_id__group"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["previous_checkpoint_id"],
            ["checkpoint.id"],
            name=op.f("fk__checkpoint__previous_checkpoint_id__checkpoint"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__checkpoint")),
        sa.UniqueConstraint(
            "group_id",
            "document_uri",
            "previous_checkpoint_id",
            name="uq__checkpoint__group_id__document_uri__previous_checkpoint_id",
            postgresql_nulls_not_distinct=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("checkpoint")
