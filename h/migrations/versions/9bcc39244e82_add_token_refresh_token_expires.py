"""
Add token refresh_token_expires.

Revision ID: 9bcc39244e82
Revises: 74bff6a7d9de
Create Date: 2017-08-02 15:19:39.710878
"""

import sqlalchemy as sa
from alembic import op

revision = "9bcc39244e82"
down_revision = "74bff6a7d9de"


def upgrade():
    op.add_column(
        "token", sa.Column("refresh_token_expires", sa.DateTime, nullable=True)
    )


def downgrade():
    op.drop_column("token", "refresh_token_expires")
