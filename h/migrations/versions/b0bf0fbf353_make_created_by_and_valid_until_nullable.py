"""Make activation.{created_by,valid_until} nullable

This will make it easier to remove these columns in a later migration.

Revision ID: b0bf0fbf353
Revises: ef3059e0396
Create Date: 2015-09-30 15:14:03.050955

"""

# revision identifiers, used by Alembic.
revision = 'b0bf0fbf353'
down_revision = 'ef3059e0396'

import datetime

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('activation') as batch_op:
        batch_op.alter_column('created_by',
                              existing_type=sa.Unicode(length=30),
                              nullable=True)
        batch_op.alter_column('valid_until',
                              existing_type=sa.DateTime,
                              nullable=True)


def downgrade():
    with op.batch_alter_table('activation') as batch_op:
        batch_op.execute(
            'UPDATE activation SET created_by = "web"')

        batch_op.alter_column('created_by',
                              existing_type=sa.Unicode(length=30),
                              nullable=False)

        in_three_days = datetime.datetime.now() + datetime.timedelta(days=3)
        in_three_days = in_three_days.strftime('%Y-%m-%d %H:%M:%S')
        batch_op.execute(
            'UPDATE activation SET valid_until = "{in_three_days}"'.format(
                in_three_days=in_three_days))

        batch_op.alter_column('valid_until',
                              existing_type=sa.DateTime,
                              nullable=False)
