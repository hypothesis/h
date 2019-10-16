"""Make group.organization_id not nullable."""
from alembic import op

revision = "f052da9df33b"
down_revision = "615358b6c428"


def upgrade():
    op.alter_column("group", "organization_id", nullable=False)


def downgrade():
    op.alter_column("group", "organization_id", nullable=True)
