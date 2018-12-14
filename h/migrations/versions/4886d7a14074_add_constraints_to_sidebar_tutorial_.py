"""Add constraints to user.sidebar_tutorial_dismissed column.

Revision ID: 4886d7a14074
Revises: 6f6a853fa2a
Create Date: 2016-01-07 12:51:33.807404

"""

# revision identifiers, used by Alembic.
revision = "4886d7a14074"
down_revision = "6f6a853fa2a"

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column("user", "sidebar_tutorial_dismissed", nullable=False)
    op.alter_column(
        "user", "sidebar_tutorial_dismissed", server_default=sa.sql.expression.false()
    )


def downgrade():
    op.alter_column("user", "sidebar_tutorial_dismissed", server_default=None)
    op.alter_column("user", "sidebar_tutorial_dismissed", nullable=True)
