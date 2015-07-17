"""Add the admin column to the user table.

Revision ID: 282e64227e98
Revises: 28eb759fccb5
Create Date: 2015-07-14 13:48:22.043892

"""

# revision identifiers, used by Alembic.
revision = '282e64227e98'
down_revision = '28eb759fccb5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('admin', sa.BOOLEAN, nullable=False,
                            server_default=sa.sql.expression.false()))


def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('admin')
