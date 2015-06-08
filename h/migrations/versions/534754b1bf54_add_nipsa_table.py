"""Add the nipsa table.

Revision ID: 534754b1bf54
Revises: 49764e8a7e69
Create Date: 2015-07-17 12:51:53.582010

"""

# revision identifiers, used by Alembic.
revision = '534754b1bf54'
down_revision = '49764e8a7e69'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'nipsa',
        sa.Column('user_id', sa.UnicodeText, primary_key=True, index=True)
    )


def downgrade():
    op.drop_table('nipsa')
