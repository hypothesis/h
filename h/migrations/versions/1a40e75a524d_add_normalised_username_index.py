"""
Add normalised username index

Revision ID: 1a40e75a524d
Revises: 02db2fa6ea98
Create Date: 2017-03-02 13:55:24.290975
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa


revision = "1a40e75a524d"
down_revision = "02db2fa6ea98"


def upgrade():
    # Creating an index concurrently does not work inside a transaction
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__user__userid"),
        "user",
        [sa.text("lower(replace(username, '.', ''))"), "authority"],
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__user__userid"), "user")
