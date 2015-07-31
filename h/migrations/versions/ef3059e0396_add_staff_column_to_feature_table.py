"""Add the staff columns to the feature and user tables.

Revision ID: ef3059e0396
Revises: 3bf1c2289e8d
Create Date: 2015-07-30 16:25:14.837823

"""

# revision identifiers, used by Alembic.
revision = 'ef3059e0396'
down_revision = '3bf1c2289e8d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('feature') as batch_op:
        batch_op.add_column(
            sa.Column('staff',
                      sa.Boolean,
                      nullable=False,
                      default=False,
                      server_default=sa.sql.expression.false()))

    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('staff', sa.Boolean, nullable=False,
                            server_default=sa.sql.expression.false()))


def downgrade():
    with op.batch_alter_table('feature') as batch_op:
        batch_op.drop_column('staff')
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('staff')
