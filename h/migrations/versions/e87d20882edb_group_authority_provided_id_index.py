"""Group authority_provided_id index."""

from alembic import op

revision = "e87d20882edb"
down_revision = "c5260187b18f"


def upgrade():
    op.drop_index("ix__group_authority", table_name="group")
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__group_authority_provided_id"),
        "group",
        ["authority_provided_id"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__group_authority_provided_id"), table_name="group")
    op.create_index("ix__group_authority", "group", ["authority"], unique=False)
