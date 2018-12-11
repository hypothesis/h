"""
add annotation moderation table

Revision ID: 50df3e6782aa
Revises: e554d862135f
Create Date: 2017-03-29 15:15:36.092486
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa

from h.db import types


revision = "50df3e6782aa"
down_revision = "e554d862135f"


def upgrade():
    op.create_table(
        "annotation_moderation",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("annotation_id", types.URLSafeUUID, nullable=False, unique=True),
        sa.ForeignKeyConstraint(
            ["annotation_id"], ["annotation.id"], ondelete="cascade"
        ),
    )


def downgrade():
    op.drop_table("annotation_moderation")
