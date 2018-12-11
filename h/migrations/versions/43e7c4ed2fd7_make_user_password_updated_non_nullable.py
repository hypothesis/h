"""make user password_updated non-nullable

Revision ID: 43e7c4ed2fd7
Revises: 530268a1937c
Create Date: 2015-12-22 15:48:14.867487

"""

# revision identifiers, used by Alembic.
revision = "43e7c4ed2fd7"
down_revision = "42bd46b9b1ea"

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column("user", "password_updated", nullable=False)


def downgrade():
    op.alter_column("user", "password_updated", nullable=True)
