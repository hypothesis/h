"""Add CASCADE on deletion for annotation_slim.document_id."""
from alembic import op

revision = "7418b43b64c3"
down_revision = "3081971a50fc"


def upgrade():
    op.drop_constraint(
        "fk__annotation_slim__document_id__document",
        "annotation_slim",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk__annotation_slim__document_id__document"),
        "annotation_slim",
        "document",
        ["document_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__annotation_slim__document_id__document"),
        "annotation_slim",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk__annotation_slim__document_id__document",
        "annotation_slim",
        "document",
        ["document_id"],
        ["id"],
    )
