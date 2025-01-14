"""Make user.pubid non-nullable."""

import sqlalchemy as sa
from alembic import op

revision = "a122e276f8d1"
down_revision = "01c9594fb9d5"


def upgrade():
    op.alter_column("user", "pubid", existing_type=sa.TEXT(), nullable=False)


def downgrade():
    op.alter_column("user", "pubid", existing_type=sa.TEXT(), nullable=True)
