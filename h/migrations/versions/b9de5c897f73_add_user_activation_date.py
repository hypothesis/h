"""Add user activation date."""

import sqlalchemy as sa
from alembic import op

revision = "b9de5c897f73"
down_revision = "8bd83598ad77"


def upgrade():
    op.add_column(
        "user",
        sa.Column("activation_date", sa.TIMESTAMP(timezone=False), nullable=True),
    )


def downgrade():
    op.drop_column("user", "activation_date")
