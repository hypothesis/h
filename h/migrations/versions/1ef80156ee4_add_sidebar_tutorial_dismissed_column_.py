"""Add the sidebar_tutorial_dismissed column to user table.

Revision ID: 1ef80156ee4
Revises: 43645baa68b2
Create Date: 2015-12-21 18:49:15.688177

"""

# revision identifiers, used by Alembic.
revision = '1ef80156ee4'
down_revision = '43e7c4ed2fd7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    try:
        op.add_column(
            'user',
            sa.Column('sidebar_tutorial_dismissed', sa.Boolean(), nullable=True))
    except Exception:
        pass

def downgrade():
    op.drop_column('user', 'sidebar_tutorial_dismissed')
