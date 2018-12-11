"""Add the text_rendered column to the annotation table

Revision ID: 39b1935d9e7b
Revises: 6b801ecc60f1
Create Date: 2016-08-09 15:19:49.572331
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa


revision = "39b1935d9e7b"
down_revision = "6b801ecc60f1"


def upgrade():
    op.add_column("annotation", sa.Column("text_rendered", sa.UnicodeText))


def downgrade():
    op.drop_column("annotation", "text_rendered")
