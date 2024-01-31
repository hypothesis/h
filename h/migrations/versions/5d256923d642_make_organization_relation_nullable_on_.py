"""Make organization relation nullable on group."""

from alembic import op

revision = "5d256923d642"
down_revision = "7fe5d688edd9"


def upgrade():
    op.alter_column("group", "organization_id", nullable=True)


def downgrade():
    op.alter_column("group", "organization_id", nullable=False)
