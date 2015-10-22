"""Add pubid column to group table

This is the first in a series of three migrations which add this new field in a
way that is safe to run on a live database.

1. Schema: add the column, nullable.
2. Data: fill in all rows missing pubids.
3. Schema: make the column non-nullable and add a uniqueness constraint.

This file represents step 1, and the two subsequent migrations steps 2 and 3.

Revision ID: 4ed50e7ac940
Revises: 5aab7692b5de
Create Date: 2015-10-22 18:18:12.530467

"""

# revision identifiers, used by Alembic.
revision = '4ed50e7ac940'
down_revision = '5aab7692b5de'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add the pubid column to the group table, but add it as nullable and
    # without the unique constraint. This is an O(1) operation.
    op.add_column('group', sa.Column('pubid', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('group', 'pubid')
