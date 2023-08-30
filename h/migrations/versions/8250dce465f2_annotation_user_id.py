"""Add user_id to the annotation table."""
import sqlalchemy as sa
from alembic import op

revision = "8250dce465f2"
down_revision = "f064c2b2e04a"


def upgrade():
    op.add_column("annotation", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix__annotation_user_id"), "annotation", ["user_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk__annotation__user_id__user"), "annotation", "user", ["user_id"], ["id"]
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__annotation__user_id__user"), "annotation", type_="foreignkey"
    )
    op.drop_index(op.f("ix__annotation_user_id"), table_name="annotation")
    op.drop_column("annotation", "user_id")
