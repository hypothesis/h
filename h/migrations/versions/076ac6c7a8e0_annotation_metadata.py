"""Add the annotation metadata table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "076ac6c7a8e0"
down_revision = "8250dce465f2"


def upgrade():
    op.create_table(
        "annotation_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("annotation_pk", sa.Integer(), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("jsonb('{}')"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["annotation_pk"],
            ["annotation.pk"],
            name=op.f("fk__annotation_metadata__annotation_pk__annotation"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__annotation_metadata")),
        sa.UniqueConstraint(
            "annotation_pk", name=op.f("uq__annotation_metadata__annotation_pk")
        ),
    )


def downgrade():
    op.drop_table("annotation_metadata")
