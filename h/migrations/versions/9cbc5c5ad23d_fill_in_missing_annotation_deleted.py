"""
Fill in missing Annotation.deleted

Revision ID: 9cbc5c5ad23d
Revises: 5bfdfde681ea
Create Date: 2016-12-19 12:41:25.269188
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa

revision = "9cbc5c5ad23d"
down_revision = "5bfdfde681ea"

annotation = sa.table("annotation", sa.column("deleted", sa.Boolean))


def upgrade():
    op.execute(
        annotation.update().where(annotation.c.deleted == None).values(deleted=False)
    )


def downgrade():
    pass
