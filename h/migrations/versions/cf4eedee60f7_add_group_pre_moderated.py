"""Add Group.pre_moderated."""

import sqlalchemy as sa
from alembic import op

revision = "cf4eedee60f7"
down_revision = "9d97a3e4921e"


def upgrade() -> None:
    op.add_column("group", sa.Column("pre_moderated", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("group", "pre_moderated")
