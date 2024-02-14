"""Make token.userid nullable."""

from alembic import op

revision = "2127515df829"
down_revision = "dad491955830"


def upgrade():
    op.alter_column("token", "userid", nullable=True)


def downgrade():
    op.alter_column("token", "userid", nullable=False)
