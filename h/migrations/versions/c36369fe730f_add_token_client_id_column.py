"""
Add token.client_id column

Revision ID: c36369fe730f
Revises: e15e47228c43
Create Date: 2016-10-19 15:24:13.387546
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c36369fe730f"
down_revision = "e15e47228c43"


def upgrade():
    op.add_column(
        "token",
        sa.Column(
            "authclient_id",
            postgresql.UUID(),
            sa.ForeignKey("authclient.id", ondelete="cascade"),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("token", "authclient_id")
