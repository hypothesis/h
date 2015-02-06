"""Add uid column to user table

Revision ID: 4a97f680ecca
Revises: 209c3cd1a864
Create Date: 2015-02-05 14:27:01.109504

"""

# revision identifiers, used by Alembic.
revision = '4a97f680ecca'
down_revision = '209c3cd1a864'

from alembic import op
import sqlalchemy as sa

users = sa.Table(
    'user',
    sa.MetaData(),
    sa.Column('username', sa.Unicode(30)),
    sa.Column('uid', sa.Unicode(30)),
)


def upgrade():
    op.add_column('user', sa.Column('uid',
                                    sa.Unicode(30),
                                    unique=True))
    op.execute(
        users.update().where(
            users.c.uid == None
        ).values(
            uid=sa.func.lower(sa.func.replace(users.c.username, '.', ''))
        )
    )
    op.alter_column('user', 'uid', nullable=False)


def downgrade():
    op.drop_column('user', 'uid')
