"""
Remove uniqueness constraint on token.userid.

Revision ID: e15e47228c43
Revises: 5dce9a8c42c2
Create Date: 2016-10-19 16:17:06.067310
"""

from alembic import op

revision = "e15e47228c43"
down_revision = "5dce9a8c42c2"


def upgrade():
    op.drop_constraint("uq__token__userid", "token")


def downgrade():
    op.create_unique_constraint("uq__token__userid", "token", ["userid"])
