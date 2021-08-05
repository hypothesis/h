"""
Create annotation table.

Revision ID: 4c0c44605c09
Revises: 4886d7a14074
Create Date: 2016-01-20 12:58:16.249481

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from h.db import types

# revision identifiers, used by Alembic.
revision = "4c0c44605c09"
down_revision = "21f87f395e26"


def upgrade():
    op.create_table(
        "annotation",
        sa.Column(
            "id",
            types.URLSafeUUID,
            server_default=sa.func.uuid_generate_v1mc(),
            primary_key=True,
        ),
        sa.Column("created", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("userid", sa.UnicodeText(), nullable=False),
        sa.Column(
            "groupid", sa.UnicodeText(), server_default="__world__", nullable=False
        ),
        sa.Column("text", sa.UnicodeText(), nullable=True),
        sa.Column(
            "tags", postgresql.ARRAY(sa.UnicodeText, zero_indexes=True), nullable=True
        ),
        sa.Column(
            "shared",
            sa.Boolean,
            server_default=sa.sql.expression.false(),
            nullable=False,
        ),
        sa.Column("target_uri", sa.UnicodeText(), nullable=False),
        sa.Column("target_uri_normalized", sa.UnicodeText(), nullable=False),
        sa.Column(
            "target_selectors",
            postgresql.JSONB,
            server_default=sa.func.jsonb("[]"),
            nullable=True,
        ),
        sa.Column(
            "references",
            postgresql.ARRAY(types.URLSafeUUID),
            server_default=sa.text("ARRAY[]::uuid[]"),
            nullable=True,
        ),
        sa.Column("extra", postgresql.JSONB, nullable=True),
    )
    op.create_index(
        op.f("ix__annotation_groupid"), "annotation", ["groupid"], unique=False
    )
    op.create_index(
        op.f("ix__annotation_tags"),
        "annotation",
        ["tags"],
        postgresql_using="gin",
        unique=False,
    )
    op.create_index(
        op.f("ix__annotation_userid"), "annotation", ["userid"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix__annotation_userid"), table_name="annotation")
    op.drop_index(op.f("ix__annotation_tags"), table_name="annotation")
    op.drop_index(op.f("ix__annotation_groupid"), table_name="annotation")
    op.drop_table("annotation")
