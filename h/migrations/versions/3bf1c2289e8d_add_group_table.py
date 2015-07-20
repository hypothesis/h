"""Add group table

Revision ID: 3bf1c2289e8d
Revises: 282e64227e98
Create Date: 2015-07-20 11:50:11.639973

"""

# revision identifiers, used by Alembic.
revision = '3bf1c2289e8d'
down_revision = '282e64227e98'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('group',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=100), nullable=False),
        sa.Column('created', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['creator_id'], ['user.id'])
    )
    op.create_table('user_group',
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['group.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'])
    )


def downgrade():
    op.drop_table('user_group')
    op.drop_table('group')
