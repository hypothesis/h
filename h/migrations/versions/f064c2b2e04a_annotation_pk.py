"""Add pk to the annotation table."""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.schema import CreateSequence, DropSequence, Sequence

revision = "f064c2b2e04a"
down_revision = "95825c951c08"


def upgrade():
    op.execute(CreateSequence(Sequence("annotation_id_seq")))
    op.add_column("annotation", sa.Column("pk", sa.Integer(), nullable=True))

    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")
    # Create index for the constraint first, concurrently
    op.execute(
        """CREATE UNIQUE INDEX CONCURRENTLY ix__annotation__pk ON annotation (pk);"""
    )
    # Use the now existing index to create the constraint. It will be renamed in this process
    op.execute(
        """ALTER TABLE annotation ADD CONSTRAINT uq__annotation__pk UNIQUE USING INDEX ix__annotation__pk;"""
    )


def downgrade():
    op.drop_constraint(op.f("uq__annotation__pk"), "annotation", type_="unique")
    op.drop_column("annotation", "pk")
    op.execute(DropSequence(Sequence("annotation_id_seq")))
