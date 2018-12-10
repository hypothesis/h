# -*- coding: utf-8 -*-
"""Add enforce_scope column to group table"""
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from alembic import op
import sqlalchemy as sa


revision = "2d0ad2b1bf07"
down_revision = "5ed9c8c105f6"


def upgrade():
    op.add_column(
        "group",
        sa.Column(
            "enforce_scope",
            sa.Boolean(),
            server_default=sa.sql.expression.true(),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("group", "enforce_scope")
