"""Add user.deleted column."""

from alembic import op
from sqlalchemy import Boolean, Column, sql

revision = "22a9ef7407ee"
down_revision = "08d3c5a8bd08"


def upgrade():
    op.add_column(
        "user",
        Column(
            "deleted",
            Boolean,
            default=False,
            nullable=False,
            server_default=sql.expression.false(),
        ),
    )


def downgrade():
    op.drop_column("user", "deleted")
