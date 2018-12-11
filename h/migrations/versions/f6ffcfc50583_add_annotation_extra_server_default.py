"""add annotation.extra server default

Revision ID: f6ffcfc50583
Revises: 98157e28a7e1
Create Date: 2016-06-06 15:14:36.642775

"""

# revision identifiers, used by Alembic.
revision = "f6ffcfc50583"
down_revision = "98157e28a7e1"

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column("annotation", "extra", server_default=sa.func.jsonb("{}"))


def downgrade():
    op.alter_column("annotation", "extra", server_default=None)
