"""Remove created_by and valid_until columns

Revision ID: 32efc6033dd1
Revises: 14a8ee5bc8da
Create Date: 2015-09-25 18:40:40.325527

"""

# revision identifiers, used by Alembic.
revision = '32efc6033dd1'
down_revision = '14a8ee5bc8da'

import datetime

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('activation') as batch_op:
        batch_op.drop_column('created_by')
        batch_op.drop_column('valid_until')


def downgrade():
    with op.batch_alter_table('activation') as batch_op:
        batch_op.add_column(sa.Column('created_by',
                            sa.Unicode(30),
                            nullable=True))

        in_three_days = datetime.datetime.now() + datetime.timedelta(days=3)
        in_three_days = in_three_days.strftime('%Y-%m-%d %H:%M:%S')
        batch_op.add_column(sa.Column('valid_until',
                            sa.DateTime,
                            nullable=True))
