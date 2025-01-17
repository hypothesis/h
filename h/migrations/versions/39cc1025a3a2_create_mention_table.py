"""Add migration to create Mention table."""

import sqlalchemy as sa
from alembic import op

revision = "39cc1025a3a2"
down_revision = "78d3d6fe1d42"


def upgrade():
    op.create_table(
        "mention",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("annotation_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["annotation_id"],
            ["annotation_slim.id"],
            name=op.f("fk__mention__annotation_id__annotation_slim"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__mention__user_id__user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__mention")),
    )
    op.create_index(op.f("ix__mention_user_id"), "mention", ["user_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix__mention_user_id"), table_name="mention")
    op.drop_table("mention")
