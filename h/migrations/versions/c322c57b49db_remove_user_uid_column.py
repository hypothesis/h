"""
Remove user uid column

Revision ID: c322c57b49db
Revises: 18dfed902c9e
Create Date: 2017-03-03 12:24:19.739583
"""

import sqlalchemy as sa
from alembic import op

revision = "c322c57b49db"
down_revision = "18dfed902c9e"


def upgrade():
    op.drop_column("user", "uid")


def downgrade():
    op.add_column("user", sa.Column("uid", sa.UnicodeText(), nullable=True))
