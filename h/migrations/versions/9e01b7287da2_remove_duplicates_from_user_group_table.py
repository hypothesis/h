"""
Remove duplicate rows from the user_group table.

Revision ID: 9e01b7287da2
Revises: 6f86796f64e0
Create Date: 2016-07-08 17:54:57.399139
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "9e01b7287da2"
down_revision = "6f86796f64e0"

Session = sessionmaker()


user_group = sa.table(
    "user_group", sa.Column("user_id", sa.Integer), sa.Column("group_id", sa.Integer)
)


def upgrade():
    session = Session(bind=op.get_bind())

    # Find all the groups of duplicate user_group rows that have the same
    # user_id and group_id values.
    groups = (
        session.query(user_group)
        .group_by("user_id", "group_id")
        .having(sa.func.count("*") > 1)
    )

    for user_id, group_id in groups:
        # Delete all the rows from the group of duplicate rows.
        # This deletes _all_ the rows from the group, we'll have to put back
        # one row later.
        session.execute(
            user_group.delete()
            .where(user_group.c.user_id == user_id)
            .where(user_group.c.group_id == group_id)
        )

        # Re-insert one row in place of the deleted group of duplicate rows.
        session.execute(user_group.insert().values(user_id=user_id, group_id=group_id))


def downgrade():
    pass
