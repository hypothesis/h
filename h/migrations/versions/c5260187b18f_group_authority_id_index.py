"""Create index on Group.authority_provided_id."""

from alembic import op

revision = "c5260187b18f"
down_revision = "63e2559e0339"


def upgrade():
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__group_authority"),
        "group",
        ["authority"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__group_authority"), table_name="group")
