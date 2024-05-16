"""Add ON DELETE CASCADE to user_group.group_id."""

from alembic import op

revision = "857c71c8f5f3"
down_revision = "22a9ef7407ee"


def upgrade():
    op.drop_constraint(
        "fk__user_group__group_id__group", "user_group", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk__user_group__group_id__group",
        "user_group",
        "group",
        ["group_id"],
        ["id"],
        ondelete="cascade",
    )


def downgrade():
    op.drop_constraint(
        "fk__user_group__group_id__group", "user_group", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk__user_group__group_id__group", "user_group", "group", ["group_id"], ["id"]
    )
