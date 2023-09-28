"""Add CASCADE on deletion for annotation_slim.group."""
from alembic import op

revision = "0d101aa6b9a5"
down_revision = "28a982795769"


def upgrade():
    op.drop_constraint(
        "fk__annotation_slim__group_id__group", "annotation_slim", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk__annotation_slim__group_id__group"),
        "annotation_slim",
        "group",
        ["group_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__annotation_slim__group_id__group"),
        "annotation_slim",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk__annotation_slim__group_id__group",
        "annotation_slim",
        "group",
        ["group_id"],
        ["id"],
    )
