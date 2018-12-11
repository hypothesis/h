"""
Relax password constraints

Revision ID: 504a6a4db06d
Revises: de42d613c18d
Create Date: 2016-08-18 22:32:51.092582
"""

from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op


revision = "504a6a4db06d"
down_revision = "de42d613c18d"


def upgrade():
    op.alter_column("user", "password", nullable=True)
    op.alter_column("user", "password_updated", nullable=True, server_default=None)
    op.alter_column("user", "salt", nullable=True)


def downgrade():
    op.alter_column("user", "password", nullable=False)
    op.alter_column(
        "user", "password_updated", nullable=False, server_default=sa.func.now()
    )
    op.alter_column("user", "salt", nullable=False)
