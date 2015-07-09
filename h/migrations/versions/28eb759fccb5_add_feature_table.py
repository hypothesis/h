"""Add feature table

Revision ID: 28eb759fccb5
Revises: 29d0200ba8a9
Create Date: 2015-07-08 15:53:26.103767

"""

# revision identifiers, used by Alembic.
revision = '28eb759fccb5'
down_revision = '29d0200ba8a9'

import os

from alembic import op
from pyramid.settings import asbool
import sqlalchemy as sa


def upgrade():
    feature_table = op.create_table('feature',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=50), nullable=False),
        sa.Column('everyone', sa.Boolean(), server_default=sa.sql.expression.false(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'))

    op.bulk_insert(feature_table, [
        {'name': u'claim',
         'everyone': asbool(os.environ.get('FEATURE_CLAIM'))},
        {'name': u'notification',
         'everyone': asbool(os.environ.get('FEATURE_NOTIFICATION'))},
        {'name': u'queue',
         'everyone': asbool(os.environ.get('FEATURE_QUEUE'))},
        {'name': u'streamer',
         'everyone': asbool(os.environ.get('FEATURE_STREAMER'))}])


def downgrade():
    op.drop_table('feature')
