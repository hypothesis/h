"""Create index on annotation_slim.document_id."""

from alembic import op

revision = "ecf91905c143"
down_revision = "1671cf35fb34"


def upgrade():
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__annotation_slim_document_id"),
        "annotation_slim",
        ["document_id"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__annotation_slim_document_id"), table_name="annotation_slim")
