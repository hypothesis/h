"""Add email and name columns to user_identity.

Revision ID: 5cb1ef58e3ca
Revises: ec5c9a864c76
"""

from alembic import op
from sqlalchemy import Column, UnicodeText

revision = "5cb1ef58e3ca"
down_revision = "ec5c9a864c76"


def upgrade():
    op.add_column("user_identity", Column("email", UnicodeText()))
    op.add_column("user_identity", Column("name", UnicodeText()))
    op.add_column("user_identity", Column("given_name", UnicodeText()))
    op.add_column("user_identity", Column("family_name", UnicodeText()))


def downgrade():
    op.drop_column("user_identity", "email")
    op.drop_column("user_identity", "name")
    op.drop_column("user_identity", "given_name")
    op.drop_column("user_identity", "family_name")
