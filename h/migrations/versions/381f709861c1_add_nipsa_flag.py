"""Add nipsa flag

Revision ID: 381f709861c1
Revises: 4a97f680ecca
Create Date: 2015-05-06 13:24:29.679068

"""

# revision identifiers, used by Alembic.
revision = '381f709861c1'
down_revision = '4a97f680ecca'

from alembic import op
import sqlalchemy as sa

users = sa.Table(
    'user',
    sa.MetaData(),
    sa.Column('nipsa', sa.BOOLEAN),
)


def upgrade():
    op.add_column('user', sa.Column('nipsa',
                                    sa.BOOLEAN,
                                    default=False))
    op.execute(
        users.update().where(
            users.c.nipsa == None
        ).values(
            nipsa=False
        )
    )

    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('nipsa', nullable=False)


def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('nipsa')
