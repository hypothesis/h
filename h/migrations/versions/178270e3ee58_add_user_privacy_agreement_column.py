"""
Add user privacy agreement column.

Add a column to track user's most recent acceptance of privacy policy
"""

import sqlalchemy as sa
from alembic import op

revision = "178270e3ee58"
down_revision = "f052da9df33b"


def upgrade():
    op.add_column("user", sa.Column("privacy_accepted", sa.DateTime, nullable=True))


def downgrade():
    op.drop_column("user", "privacy_accepted")
