"""
Remove unused user indices

Revision ID: 18dfed902c9e
Revises: 7e2443f8d7d6
Create Date: 2017-03-03 12:13:16.122752
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa


revision = "18dfed902c9e"
down_revision = "7e2443f8d7d6"


def upgrade():
    op.drop_constraint("uq__user__uid", "user")
    op.drop_constraint("uq__user__username", "user")
    op.drop_index(op.f("ix__user__authority"), "user")


def downgrade():
    op.execute("COMMIT")

    op.create_index(
        op.f("ix__user__authority"), "user", ["authority"], postgresql_concurrently=True
    )

    # We add the index back first, and then create a constraint from the
    # index, to avoid holding the table locked for the entire time the index
    # is building.
    op.create_index(
        op.f("uq__user__uid"),
        "user",
        ["uid", "authority"],
        unique=True,
        postgresql_concurrently=True,
    )
    op.execute(
        sa.text(
            'ALTER TABLE "user" ADD CONSTRAINT uq__user__uid UNIQUE USING INDEX uq__user__uid'
        )
    )

    op.create_index(
        op.f("uq__user__username"),
        "user",
        ["username", "authority"],
        unique=True,
        postgresql_concurrently=True,
    )
    op.execute(
        sa.text(
            'ALTER TABLE "user" ADD CONSTRAINT uq__user__username UNIQUE USING INDEX uq__user__username'
        )
    )
