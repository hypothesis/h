"""Create the annotation_metatada table."""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "34c8067db0ee"
down_revision = "7418b43b64c3"


def upgrade():
    op.create_table(
        "annotation_metadata",
        sa.Column("annotation_id", sa.Integer(), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("jsonb('{}')"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["annotation_id"],
            ["annotation_slim.id"],
            name=op.f("fk__annotation_metadata__annotation_id__annotation_slim"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("annotation_id", name=op.f("pk__annotation_metadata")),
        sa.UniqueConstraint(
            "annotation_id", name=op.f("uq__annotation_metadata__annotation_id")
        ),
    )


def downgrade():
    op.drop_table("annotation_metadata")
