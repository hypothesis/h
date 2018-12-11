"""Add index to group.name column

Revision ID: 21f87f395e26
Revises: 0d4755a0d88b
Create Date: 2016-03-24 15:12:59.803179

"""

# revision identifiers, used by Alembic.
revision = "21f87f395e26"
down_revision = "0d4755a0d88b"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Creating a concurrent index does not work inside a transaction
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__group__name"), "group", ["name"], postgresql_concurrently=True
    )


def downgrade():
    op.drop_index(op.f("ix__group__name"), "group")
