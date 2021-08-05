"""
Fill in user.sidebar_tutorial_dismissed column default values.

Revision ID: 6f6a853fa2a
Revises: 1ef80156ee4
Create Date: 2016-01-06 19:12:14.402260

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm

# revision identifiers, used by Alembic.
revision = "6f6a853fa2a"
down_revision = "1ef80156ee4"


Session = orm.sessionmaker()


user = sa.table("user", sa.column("sidebar_tutorial_dismissed", sa.Boolean))


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    op.execute(user.update().values(sidebar_tutorial_dismissed=True))


def downgrade():
    pass
