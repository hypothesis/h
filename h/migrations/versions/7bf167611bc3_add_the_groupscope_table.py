"""
Add the GroupScope table.

Revision ID: 7bf167611bc3
Revises: c943c3f8a7e5
Create Date: 2018-02-08 11:00:50.420618
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa

revision = '7bf167611bc3'
down_revision = 'c943c3f8a7e5'


def upgrade():
    op.create_table(
        'groupscope',
        sa.Column('id', sa.Integer, autoincrement=True, primary_key=True),
        sa.Column('hostname', sa.UnicodeText, nullable=False, unique=True),
    )
    op.create_table(
        'group_groupscope',
        sa.Column(
            'group_id', sa.Integer, sa.ForeignKey('group.id'), nullable=False),
        sa.Column(
            'groupscope_id',
            sa.Integer,
            sa.ForeignKey('groupscope.id'),
            nullable=False),
        sa.PrimaryKeyConstraint('group_id', 'groupscope_id'),
    )


def downgrade():
    op.drop_table('group_groupscope')
    op.drop_table('groupscope')
