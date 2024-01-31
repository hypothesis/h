"""Make user.email nullable."""

from alembic import op

revision = "792debe852c3"
down_revision = "2a414b3393be"


def upgrade():
    op.alter_column("user", "email", nullable=True)


def downgrade():
    op.alter_column("user", "email", nullable=False)
