"""Add CASCADE on deletion for annotation_slim.user."""
from alembic import op

revision = "28a982795769"
down_revision = "15b5dc900ebb"


def upgrade():
    op.drop_constraint(
        "fk__annotation_slim__user_id__user", "annotation_slim", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk__annotation_slim__user_id__user"),
        "annotation_slim",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__annotation_slim__user_id__user"),
        "annotation_slim",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk__annotation_slim__user_id__user",
        "annotation_slim",
        "user",
        ["user_id"],
        ["id"],
    )
