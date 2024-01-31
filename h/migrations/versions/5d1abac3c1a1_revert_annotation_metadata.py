"""Revert annotation_metadatai."""

from alembic import op
from sqlalchemy.dialects import postgresql

revision = "5d1abac3c1a1"
down_revision = "6df1c8c3e423"


def upgrade():
    op.drop_table("annotation_metadata")


def downgrade():
    """No downgrade, see orignal migration 5d1abac3c1a1."""
    pass
