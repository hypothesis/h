"""Make token.user_id not nullable."""

from alembic import op

revision = "dad491955830"
down_revision = "8e3417e3713b"


def upgrade():
    op.alter_column("token", "user_id", nullable=False)


def downgrade():
    op.alter_column("token", "user_id", nullable=True)
