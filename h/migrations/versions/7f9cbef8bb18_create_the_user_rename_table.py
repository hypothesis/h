"""Create the user_rename table."""

import sqlalchemy as sa
from alembic import op

revision = "7f9cbef8bb18"
down_revision = "550865ed6622"


def upgrade() -> None:
    op.create_table(
        "user_rename",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("old_userid", sa.String(), nullable=False),
        sa.Column("new_userid", sa.String(), nullable=False),
        sa.Column(
            "requested_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("requested_by", sa.String(), nullable=False),
        sa.Column("tag", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__user_rename__user_id__user"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__user_rename")),
    )


def downgrade() -> None:
    op.drop_table("user_rename")
