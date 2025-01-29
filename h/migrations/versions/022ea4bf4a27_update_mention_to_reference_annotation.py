"""Update mention to reference annotation.

Revision ID: 022ea4bf4a27
Revises: 39cc1025a3a2
"""

import sqlalchemy as sa
from alembic import op

from h.db import types

revision = "022ea4bf4a27"
down_revision = "39cc1025a3a2"


def upgrade() -> None:
    op.drop_column("mention", "annotation_id")
    op.add_column(
        "mention",
        sa.Column(
            "annotation_id",
            types.URLSafeUUID(),
            sa.ForeignKey("annotation.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("mention", "annotation_id")
    op.add_column(
        "mention",
        sa.Column(
            "annotation_id",
            sa.INTEGER(),
            sa.ForeignKey("annotation_slim.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
