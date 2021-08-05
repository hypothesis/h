"""
Add index to user authority column.

Revision ID: afd433075707
Revises: 504a6a4db06d
Create Date: 2016-08-19 14:26:08.706027
"""
from alembic import op

revision = "afd433075707"
down_revision = "504a6a4db06d"


def upgrade():
    # Creating a concurrent index does not work inside a transaction
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__user__authority"), "user", ["authority"], postgresql_concurrently=True
    )


def downgrade():
    op.drop_index(op.f("ix__user__authority"), "user")
