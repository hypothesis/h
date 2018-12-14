"""
Add the organization table.

Revision ID: 628c53b07
Revises: 7bf167611bc3
Create Date: 2018-03-15 11:00:50.420618
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa

revision = "628c53b07"
down_revision = "7bf167611bc3"


def upgrade():
    op.create_table(
        "organization",
        sa.Column("id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("created", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.UnicodeText, nullable=False, index=True),
        sa.Column("logo", sa.UnicodeText),
        sa.Column("authority", sa.UnicodeText, nullable=False),
        sa.Column("pubid", sa.Text, unique=True, nullable=False),
    )


def downgrade():
    op.drop_table("organization")
