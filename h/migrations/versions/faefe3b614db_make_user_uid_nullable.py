"""
Make user uid nullable.

Revision ID: faefe3b614db
Revises: 1a40e75a524d
Create Date: 2017-03-02 14:17:41.708781
"""

import sqlalchemy as sa
from alembic import op

revision = "faefe3b614db"
down_revision = "1a40e75a524d"

user = sa.table(
    "user", sa.column("username", sa.UnicodeText()), sa.column("uid", sa.UnicodeText())
)


def upgrade():
    op.alter_column("user", "uid", nullable=True)


def downgrade():
    # Backfill the uid column for any users that were created before this was
    # rolled back.
    op.execute(
        user.update()
        .where(user.c.uid == None)  # noqa: E711
        .values(uid=sa.func.lower(sa.func.replace(user.c.username, ".", "")))
    )
    op.alter_column("user", "uid", nullable=False)
