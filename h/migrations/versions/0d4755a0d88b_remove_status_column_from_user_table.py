"""
Remove status column from user table.

Revision ID: 0d4755a0d88b
Revises: 2494fea98d2d
Create Date: 2016-03-21 20:07:07.002482

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0d4755a0d88b"
down_revision = "2494fea98d2d"


def upgrade():
    # Dropping a column is O(1) so this is safe to run against a production
    # database.
    op.drop_column("user", "status")


def downgrade():
    op.add_column("user", sa.Column("status", sa.Integer()))
