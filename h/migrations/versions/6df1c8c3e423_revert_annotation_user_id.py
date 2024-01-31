"""Revert annotation.user_id."""

from alembic import op

revision = "6df1c8c3e423"
down_revision = "076ac6c7a8e0"


def upgrade():
    op.drop_index("ix__annotation_user_id", table_name="annotation")
    op.drop_constraint(
        "fk__annotation__user_id__user", "annotation", type_="foreignkey"
    )
    op.drop_column("annotation", "user_id")


def downgrade():
    """No downgrade, see the upgrade for migration 8250dce465f2."""
    pass
