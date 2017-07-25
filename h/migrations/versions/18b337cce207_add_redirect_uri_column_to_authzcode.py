"""
Add redirect_uri column to authzcode

Revision ID: 18b337cce207
Revises: a2295c2bbe29
Create Date: 2017-07-21 13:43:43.917958
"""

from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op

revision = '18b337cce207'
down_revision = 'a2295c2bbe29'


def upgrade():
    op.add_column('authzcode', sa.Column('redirect_uri', sa.UnicodeText(), nullable=False))


def downgrade():
    op.drop_column('authzcode', 'redirect_uri')
