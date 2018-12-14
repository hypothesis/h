# -*- coding: utf-8 -*-
"""Add index to user.nipsa"""
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from alembic import op
import sqlalchemy as sa


revision = "7fe5d688edd9"
down_revision = "792debe852c3"


def upgrade():
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__user__nipsa"),
        "user",
        ["nipsa"],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where=sa.text("nipsa is true"),
    )


def downgrade():
    op.drop_index(op.f("ix__user__nipsa"), table_name="user")
