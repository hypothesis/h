"""
Add annotation.updated index.

Revision ID: fde6cdcdd39a
Revises: 3bcd62dd7260
Create Date: 2016-04-27 13:42:14.201644

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fde6cdcdd39a"
down_revision = "3bcd62dd7260"


def upgrade():
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__annotation_updated"),
        "annotation",
        ["updated"],
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__annotation_updated"), "annotation")
