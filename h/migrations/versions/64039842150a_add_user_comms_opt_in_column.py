"""Add User.comms_opt_in column."""

import sqlalchemy as sa
from alembic import op

revision = "64039842150a"
down_revision = "3359d7d8ec29"


def upgrade():
    op.add_column("user", sa.Column("comms_opt_in", sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column("user", "comms_opt_in")
