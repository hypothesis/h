"""add cohort table

Revision ID: 3bcd62dd7260
Revises: dfa82518915a
Create Date: 2016-05-10 17:01:02.704596

"""

# revision identifiers, used by Alembic.
revision = '3bcd62dd7260'
down_revision = 'dfa82518915a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('cohort',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=100), nullable=False),
        sa.Column('created', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('user_cohort',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('cohort_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['cohort_id'], ['cohort.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'])
    )


def downgrade():
    op.drop_table('user_cohort')
    op.drop_table('cohort')
