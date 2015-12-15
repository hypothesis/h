"""Add password last updated column to accounts model

Revision ID: 530268a1937c
Revises: 43645baa68b2
Create Date: 2015-12-14 17:07:44.757878

"""

# revision identifiers, used by Alembic.
revision = '530268a1937c'
down_revision = '43645baa68b2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('last_password_update',
                                    sa.DateTime(timezone=False),
                                    default=sa.sql.func.now(),
                                    server_default=sa.func.now(),
                                    nullable=True))


def downgrade():
    op.drop_column('user', 'last_password_update')
