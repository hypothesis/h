"""
Make annotation.extra non-nullable.

Revision ID: 98157e28a7e1
Revises: 77c2af032aca
Create Date: 2016-06-06 14:52:41.277688

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "98157e28a7e1"
down_revision = "77c2af032aca"


def upgrade():
    op.alter_column("annotation", "extra", nullable=False)


def downgrade():
    op.alter_column("annotation", "extra", nullable=True)
