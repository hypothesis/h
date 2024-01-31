"""
Fill in missing password_updated fields.

Revision ID: 42bd46b9b1ea
Revises: 43e7c4ed2fd7
Create Date: 2016-01-07 14:20:44.094611

"""

import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import sessionmaker

# revision identifiers, used by Alembic.
revision = "42bd46b9b1ea"
down_revision = None


Session = sessionmaker()

user = sa.table(
    "user", sa.column("id", sa.Integer), sa.column("password_updated", sa.DateTime)
)


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    # Add the password_updated field to each row lacking one.
    # This is O(N) but does not lock the whole table.
    for id_, _ in session.query(user).all():
        op.execute(
            user.update()
            .where(user.c.id == id_)
            .where(user.c.password_updated == None)  # noqa: E711
            .values(password_updated=datetime.datetime.utcnow())
        )


def downgrade():
    # Nothing to do here.
    pass
