"""
Create authzcode table

Revision ID: 0d1b3fd8807c
Revises: b980b1a8f6af
Create Date: 2017-07-10 12:04:28.328864
"""

from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0d1b3fd8807c"
down_revision = "b980b1a8f6af"


def upgrade():
    op.create_table(
        "authzcode",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, primary_key=True, nullable=False
        ),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires", sa.DateTime(), nullable=False),
        sa.Column("code", sa.UnicodeText, nullable=False),
        sa.Column("authclient_id", postgresql.UUID(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["authclient_id"], ["authclient.id"]),
    )
    op.create_index(op.f("uq__authzcode__code"), "authzcode", ["code"], unique=True)


def downgrade():
    op.drop_index(op.f("uq__authzcode__code"), table_name="authzcode")
    op.drop_table("authzcode")
