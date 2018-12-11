# -*- coding: utf-8 -*-
"""Make organization relation nullable on group"""
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from alembic import op


revision = "5d256923d642"
down_revision = "7fe5d688edd9"


def upgrade():
    op.alter_column("group", "organization_id", nullable=True)


def downgrade():
    op.alter_column("group", "organization_id", nullable=False)
