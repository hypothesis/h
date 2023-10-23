"""Add "user" index for email."""
import sqlalchemy as sa
from alembic import op

revision = "0de98307b3c0"
down_revision = "34c8067db0ee"


def upgrade():
    op.execute("COMMIT")  # For the concurrent index creation
    op.create_index(
        op.f("ix__user__email"),
        "user",
        [sa.text("lower('email')")],
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__user__email"), "user")
