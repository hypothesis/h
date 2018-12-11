"""Create document tables

Revision ID: dfa82518915a
Revises: 4c0c44605c09
Create Date: 2016-02-10 14:52:08.236839

"""

# revision identifiers, used by Alembic.
revision = "dfa82518915a"
down_revision = "4c0c44605c09"

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table(
        "document",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "document_meta",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("claimant", sa.UnicodeText, nullable=False),
        sa.Column("claimant_normalized", sa.UnicodeText, nullable=False),
        sa.Column("type", sa.UnicodeText, nullable=False),
        sa.Column(
            "value", postgresql.ARRAY(sa.UnicodeText, zero_indexes=True), nullable=False
        ),
        sa.Column("document_id", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(["document_id"], [u"document.id"]),
        sa.UniqueConstraint("claimant_normalized", "type"),
    )

    op.create_table(
        "document_uri",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("claimant", sa.UnicodeText, nullable=False),
        sa.Column("claimant_normalized", sa.UnicodeText, nullable=False),
        sa.Column("uri", sa.UnicodeText, nullable=False),
        sa.Column("uri_normalized", sa.UnicodeText, nullable=False, index=True),
        sa.Column("type", sa.UnicodeText, nullable=True),
        sa.Column("content_type", sa.UnicodeText, nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], [u"document.id"]),
        sa.UniqueConstraint(
            "claimant_normalized", "uri_normalized", "type", "content_type"
        ),
    )


def downgrade():
    op.drop_table("document_uri")
    op.drop_table("document_meta")
    op.drop_table("document")
