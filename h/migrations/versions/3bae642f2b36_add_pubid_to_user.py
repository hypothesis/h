"""Add pubid column to user."""

import sqlalchemy as sa
from alembic import op

revision = "3bae642f2b36"
down_revision = "9c0efdf762a6"


def upgrade():
    op.add_column("user", sa.Column("pubid", sa.Text(), nullable=True))
    op.create_unique_constraint(op.f("uq__user__pubid"), "user", ["pubid"])


def downgrade():
    op.drop_constraint(op.f("uq__user__pubid"), "user", type_="unique")
    op.drop_column("user", "pubid")
