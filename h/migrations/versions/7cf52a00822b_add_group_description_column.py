"""
Add group.description column

Revision ID: 7cf52a00822b
Revises: 9e6b4f70f588
Create Date: 2016-07-06 11:02:08.163718
"""

import sqlalchemy as sa
from alembic import op

revision = "7cf52a00822b"
down_revision = "9e6b4f70f588"


def upgrade():
    op.add_column("group", sa.Column("description", sa.UnicodeText()))


def downgrade():
    op.drop_column("group", "description")
