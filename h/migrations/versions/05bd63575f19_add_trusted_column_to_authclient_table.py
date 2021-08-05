"""
Add trusted column to authclient table.

Revision ID: 05bd63575f19
Revises: dfb8b45674db
Create Date: 2017-07-18 13:45:12.301240
"""

import sqlalchemy as sa
from alembic import op

revision = "05bd63575f19"
down_revision = "dfb8b45674db"


def upgrade():
    op.add_column(
        "authclient",
        sa.Column(
            "trusted",
            sa.Boolean(),
            server_default=sa.sql.expression.false(),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("authclient", "trusted")
