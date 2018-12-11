"""
Add index to annotation thread root

Revision ID: 9389d52b037d
Revises: b102c50b1133
Create Date: 2017-04-18 12:36:53.842280
"""

from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op

revision = "9389d52b037d"
down_revision = "b102c50b1133"


def upgrade():
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__annotation_thread_root"),
        "annotation",
        [sa.text('("references"[1])')],
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__annotation_thread_root"), "annotation")
