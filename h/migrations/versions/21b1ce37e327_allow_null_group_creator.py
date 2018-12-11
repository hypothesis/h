"""
Allow null group.creator

Revision ID: 21b1ce37e327
Revises: 9389d52b037d
Create Date: 2017-04-13 16:49:16.218511
"""

from __future__ import unicode_literals

from alembic import op


revision = "21b1ce37e327"
down_revision = "9389d52b037d"


def upgrade():
    op.alter_column("group", "creator_id", nullable=True)


def downgrade():
    op.alter_column("group", "creator_id", nullable=False)
