"""Add the blocklist table.

Revision ID: 571394188821
Revises: 2337185eae43
Create Date: 2015-10-05 17:21:37.857175

"""

# revision identifiers, used by Alembic.
revision = '571394188821'
down_revision = '2337185eae43'

from alembic import op
import sqlalchemy as sa


def upgrade():
    blocklist_table = op.create_table('blocklist',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('uri', sa.UnicodeText(), nullable=False, unique=True))


def downgrade():
    op.drop_table('blocklist')
