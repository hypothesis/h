"""
Fill user NIPSA column

Revision ID: b7117b569f8b
Revises: ddb5f0baa429
Create Date: 2016-09-16 17:03:25.264475
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm

from h.util.user import split_user

revision = "b7117b569f8b"
down_revision = "ddb5f0baa429"

Session = orm.sessionmaker()


user = sa.table(
    "user",
    sa.column("username", sa.UnicodeText),
    sa.column("authority", sa.UnicodeText),
    sa.column("nipsa", sa.Boolean),
)
nipsa = sa.table("nipsa", sa.column("userid", sa.UnicodeText))


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    op.execute(user.update().values(nipsa=False))

    # Fetch all the existing NIPSA'd userids and set the NIPSA flag on the
    # corresponding rows in the user table, if they exist.
    for (userid,) in session.query(nipsa):
        val = split_user(userid)
        op.execute(
            user.update()
            .where(
                sa.and_(
                    user.c.username == val["username"],
                    user.c.authority == val["domain"],
                )
            )
            .values(nipsa=True)
        )


def downgrade():
    pass
