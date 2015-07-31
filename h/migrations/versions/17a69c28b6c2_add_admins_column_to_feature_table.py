"""Add admins column to feature table

Revision ID: 17a69c28b6c2
Revises: 534754b1bf54
Create Date: 2015-07-24 20:23:04.898305

"""

# revision identifiers, used by Alembic.
revision = '17a69c28b6c2'
down_revision = '534754b1bf54'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    with op.batch_alter_table('feature') as batch_op:
        batch_op.add_column(sa.Column('admins',
                                      sa.Boolean,
                                      nullable=False,
                                      default=False,
                                      server_default=sa.sql.expression.false()))


def downgrade():
    with op.batch_alter_table('feature') as batch_op:
        batch_op.drop_column('admins')
