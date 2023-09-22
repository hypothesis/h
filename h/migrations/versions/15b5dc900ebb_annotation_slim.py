"""Create the annotation_slim table."""
import sqlalchemy as sa
from alembic import op

import h

revision = "15b5dc900ebb"
down_revision = "77bc5b4f2205"


def upgrade():
    op.create_table(
        "annotation_slim",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pubid", h.db.types.URLSafeUUID(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "moderated", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "shared", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document.id"],
            name=op.f("fk__annotation_slim__document_id__document"),
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__annotation_slim__group_id__group"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk__annotation_slim__user_id__user")
        ),
        sa.ForeignKeyConstraint(
            ["pubid"],
            ["annotation.id"],
            name=op.f("fk__annotation_slim__pubid__annotation"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__annotation_slim")),
        sa.UniqueConstraint("pubid", name=op.f("uq__annotation_slim__pubid")),
    )
    op.create_index(
        op.f("ix__annotation_slim_created"),
        "annotation_slim",
        ["created"],
        unique=False,
    )
    op.create_index(
        op.f("ix__annotation_slim_updated"),
        "annotation_slim",
        ["updated"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix__annotation_slim_updated"), table_name="annotation_slim")
    op.drop_index(op.f("ix__annotation_slim_created"), table_name="annotation_slim")
    op.drop_table("annotation_slim")
