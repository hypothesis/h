"""
Add `setting` table

Revision ID: 90412d879d1f
Revises: 8ae9d103551f
Create Date: 2016-12-19 13:29:39.933771
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa


revision = "90412d879d1f"
down_revision = "8ae9d103551f"


def upgrade():
    op.create_table(
        "setting",
        sa.Column("key", sa.UnicodeText(), primary_key=True),
        sa.Column("value", sa.UnicodeText()),
        sa.Column("created", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("setting")
