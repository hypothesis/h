"""Add user_group.created and updated columns."""

from alembic import op
from sqlalchemy import Column, DateTime

revision = "9c0efdf762a6"
down_revision = "59f42b6a0cd9"


def upgrade():
    op.add_column("user_group", Column("created", DateTime, index=True))
    op.add_column("user_group", Column("updated", DateTime, index=True))


def downgrade():
    op.drop_column("user_group", "updated")
    op.drop_column("user_group", "created")
