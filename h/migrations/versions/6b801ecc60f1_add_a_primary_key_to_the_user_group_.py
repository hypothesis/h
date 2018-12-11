"""
Add a primary key to the user_group table.

Revision ID: 6b801ecc60f1
Revises: e17d3ce4fcd2
Create Date: 2016-07-08 17:42:20.891383
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa


revision = "6b801ecc60f1"
down_revision = "e17d3ce4fcd2"


def upgrade():
    op.add_column("user_group", sa.Column("id", sa.Integer, primary_key=True))


def downgrade():
    op.drop_column("user_group", "id")
