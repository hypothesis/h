"""Remove the nipsa column from the user table.

Revision ID: 49764e8a7e69
Revises: 282e64227e98
Create Date: 2015-07-17 12:47:00.312123

"""

# revision identifiers, used by Alembic.
revision = '49764e8a7e69'
down_revision = '282e64227e98'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('nipsa')


def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('nipsa',
                            sa.BOOLEAN,
                            default=False,
                            server_default=sa.sql.expression.false(),
                            nullable=False))
