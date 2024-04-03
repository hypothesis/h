"""Fix indices created on a value instead of a column."""

import sqlalchemy as sa
from alembic import op

revision = "08d3c5a8bd08"
down_revision = "e87d20882edb"


def upgrade():
    # Creating a concurrent index does not work inside a transaction
    op.execute("COMMIT")

    # Drop the old, incorrect indices
    op.execute("DROP INDEX IF EXISTS ix__user__email")
    op.execute("DROP INDEX IF EXISTS subs_uri_lower_idx_subscriptions")

    op.create_index(
        "subs_uri_lower_idx_subscriptions",
        "subscriptions",
        [sa.text("lower(uri)")],
        unique=False,
        postgresql_concurrently=True,
    )
    op.create_index(
        "ix__user__email",
        "user",
        [sa.text("lower(email)")],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index("ix__user__email", table_name="user")
    op.drop_index("subs_uri_lower_idx_subscriptions", table_name="subscriptions")
