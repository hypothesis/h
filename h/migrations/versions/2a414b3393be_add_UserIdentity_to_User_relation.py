# -*- coding: utf-8 -*-
"""Add UserIdentity (many) -> User (one) relation."""
from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa

revision = "2a414b3393be"
down_revision = "5dd2dd5547a2"


def upgrade():
    op.add_column(
        "user_identity",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("user.id", ondelete="cascade"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("user_identity", "user_id")
