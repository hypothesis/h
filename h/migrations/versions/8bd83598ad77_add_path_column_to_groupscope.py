import sqlalchemy as sa
from alembic import op

revision = "8bd83598ad77"
down_revision = "2d0ad2b1bf07"


def upgrade():
    op.add_column("groupscope", sa.Column("path", sa.UnicodeText(), nullable=True))
    op.execute("COMMIT")
    # Create a composite index for origin and path for performance
    op.create_index(
        op.f("ix__groupscope__scope"),
        "groupscope",
        ["origin", "path"],
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__groupscope__scope"))
    op.drop_column("groupscope", "path")
