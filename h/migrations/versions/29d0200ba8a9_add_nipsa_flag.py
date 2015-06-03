"""Add NIPSA flag

Revision ID: 29d0200ba8a9
Revises: 4a97f680ecca
Create Date: 2015-06-03 12:04:34.940654

"""

# revision identifiers, used by Alembic.
revision = '29d0200ba8a9'
down_revision = '4a97f680ecca'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('nipsa',
                                    sa.BOOLEAN,
                                    default=False,
                                    server_default=sa.sql.expression.false(),
                                    nullable=False))


def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('nipsa')
