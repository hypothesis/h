"""
Add AuthClient table

Revision ID: bdaa06b14557
Revises: afd433075707
Create Date: 2016-09-08 14:00:17.363281
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "bdaa06b14557"
down_revision = "afd433075707"


def upgrade():
    op.create_table(
        "authclient",
        sa.Column(
            "id",
            postgresql.UUID(),
            server_default=sa.func.uuid_generate_v1mc(),
            nullable=False,
        ),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("name", sa.UnicodeText(), nullable=True),
        sa.Column("secret", sa.UnicodeText(), nullable=False),
        sa.Column("authority", sa.UnicodeText(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__authclient")),
    )


def downgrade():
    op.drop_table("authclient")
