"""Add Group.pre_moderated."""

import sqlalchemy as sa
from alembic import op

revision = "cf4eedee60f7"
down_revision = "96cde96b2fd7"


def upgrade() -> None:
    op.add_column("user_group", sa.Column("pre_moderated", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_group", "pre_moderated")
