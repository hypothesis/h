"""
Add organization_id to group table.

Revision ID: 46a22db075d5
Revises: 628c53b07
Create Date: 2018-03-21 09:47:47.642578
"""

import sqlalchemy as sa
from alembic import op

revision = "46a22db075d5"
down_revision = "628c53b07"


def upgrade():
    op.add_column(
        "group",
        sa.Column(
            "organization_id",
            sa.Integer,
            sa.ForeignKey("organization.id"),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("group", "organization_id")
