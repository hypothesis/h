"""
Make userid index unique.

Revision ID: 7e2443f8d7d6
Revises: faefe3b614db
Create Date: 2017-03-07 10:25:23.165687
"""

import sqlalchemy as sa
from alembic import op

revision = "7e2443f8d7d6"
down_revision = "faefe3b614db"


def upgrade():
    op.execute(sa.text("ALTER INDEX ix__user__userid RENAME TO ix__user__userid_old"))

    op.execute("COMMIT")
    op.create_index(
        op.f("ix__user__userid"),
        "user",
        [sa.text("lower(replace(username, '.', ''))"), "authority"],
        postgresql_concurrently=True,
        unique=True,
    )

    op.drop_index(op.f("ix__user__userid_old"))


def downgrade():
    op.execute(sa.text("ALTER INDEX ix__user__userid RENAME TO ix__user__userid_old"))

    op.execute("COMMIT")
    op.create_index(
        op.f("ix__user__userid"),
        "user",
        [sa.text("lower(replace(username, '.', ''))"), "authority"],
        postgresql_concurrently=True,
    )

    op.drop_index(op.f("ix__user__userid_old"))
