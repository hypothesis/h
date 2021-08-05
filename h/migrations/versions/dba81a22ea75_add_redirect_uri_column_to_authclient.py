"""
Add redirect_uri column to authclient.

Revision ID: dba81a22ea75
Revises: 0d1b3fd8807c
Create Date: 2017-07-12 15:17:05.036842
"""

import sqlalchemy as sa
from alembic import op

revision = "dba81a22ea75"
down_revision = "0d1b3fd8807c"


def upgrade():
    op.add_column(
        "authclient", sa.Column("redirect_uri", sa.UnicodeText(), nullable=True)
    )


def downgrade():
    op.drop_column("authclient", "redirect_uri")
