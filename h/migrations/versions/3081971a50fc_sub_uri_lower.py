"""Replace subscriptions index to be on lower(uri)."""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "3081971a50fc"
down_revision = "0d101aa6b9a5"


def upgrade():
    op.drop_index("subs_uri_idx_subscriptions", table_name="subscriptions")
    op.execute("COMMIT")  # For the concurrent index creation
    op.create_index(
        op.f("subs_uri_lower_idx_subscriptions"),
        "subscriptions",
        [sa.text("lower('uri')")],
        postgresql_concurrently=True,
        unique=False,
    )


def downgrade():
    op.create_index(
        "subs_uri_idx_subscriptions", "subscriptions", ["uri"], unique=False
    )
    op.drop_index("subs_uri_lower_idx_subscriptions", table_name="subscriptions")
