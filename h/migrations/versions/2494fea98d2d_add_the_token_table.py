"""
Add the token table.

Revision ID: 2494fea98d2d
Revises: 4886d7a14074
Create Date: 2016-02-15 11:20:00.787358

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2494fea98d2d"
down_revision = "4886d7a14074"


def upgrade():
    token_table = op.create_table(
        "token",
        sa.Column("created", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("userid", sa.UnicodeText(), nullable=False, unique=True),
        sa.Column("value", sa.UnicodeText(), index=True, nullable=False, unique=True),
    )


def downgrade():
    op.drop_table("token")
