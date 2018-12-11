"""
Add a unique constraint to the token.refresh_token column.

Revision ID: 02db2fa6ea98
Revises: c739ee2ae59c
Create Date: 2017-01-31 17:24:03.855420
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy


revision = "02db2fa6ea98"
down_revision = "c739ee2ae59c"


def upgrade():
    op.execute("COMMIT")
    try:
        op.create_unique_constraint(
            "uq__token__refresh_token", "token", ["refresh_token"]
        )
    except sqlalchemy.exc.ProgrammingError as exc:
        if 'relation "uq__token__refresh_token" already exists' not in exc.message:
            raise


def downgrade():
    op.drop_constraint("uq__token__refresh_token", "token")
