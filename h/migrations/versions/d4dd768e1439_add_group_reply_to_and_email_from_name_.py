"""Add group.reply_to and email_from_name columns.

Revision ID: d4dd768e1439
Revises: 5cb1ef58e3ca
"""

from alembic import op
from sqlalchemy import Column, UnicodeText

revision = "d4dd768e1439"
down_revision = "5cb1ef58e3ca"


def upgrade():
    op.add_column("group", Column("reply_to", UnicodeText(), nullable=True))
    op.add_column("group", Column("email_from_name", UnicodeText(), nullable=True))


def downgrade():
    op.drop_column("group", "reply_to")
    op.drop_column("group", "email_from_name")
