"""Create FK indexes for user and groups."""

from alembic import op

revision = "7bcd729defec"
down_revision = "8b4b4fdef955"


def upgrade():
    # Creating a concurrent index does not work inside a transaction
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__annotation_slim_group_id"),
        "annotation_slim",
        ["group_id"],
        unique=False,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__annotation_slim_user_id"),
        "annotation_slim",
        ["user_id"],
        unique=False,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__user_group_group_id"),
        "user_group",
        ["group_id"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__user_group_group_id"), table_name="user_group")
    op.drop_index(op.f("ix__annotation_slim_user_id"), table_name="annotation_slim")
    op.drop_index(op.f("ix__annotation_slim_group_id"), table_name="annotation_slim")
