"""
Add document web_uri column.

Revision ID: 3e1727613916
Revises: a001b7b4c78e
Create Date: 2016-09-12 13:21:56.739838
"""

import sqlalchemy as sa
from alembic import op

revision = "3e1727613916"
down_revision = "a001b7b4c78e"


def upgrade():
    op.add_column("document", sa.Column("web_uri", sa.UnicodeText()))


def downgrade():
    op.drop_column("document", "web_uri")
