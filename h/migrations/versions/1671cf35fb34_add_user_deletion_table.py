"""Add user_deletion table."""

from alembic import op
from sqlalchemy import Column, DateTime, Integer, String, text

revision = "1671cf35fb34"
down_revision = "857c71c8f5f3"


def upgrade():
    op.create_table(
        "user_deletion",
        Column("id", Integer(), primary_key=True, autoincrement=True, nullable=False),
        Column("userid", String(), nullable=False),
        Column(
            "requested_at", DateTime(), server_default=text("now()"), nullable=False
        ),
        Column("requested_by", String(), nullable=False),
        Column("tag", String(), nullable=False),
        Column("registered_date", DateTime(), nullable=False),
        Column("num_annotations", Integer(), nullable=False),
    )


def downgrade():
    op.drop_table("user_deletion")
