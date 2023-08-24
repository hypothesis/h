"""Add pk to the annotation table."""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.schema import CreateSequence, DropSequence, Sequence

revision = "f064c2b2e04a"
down_revision = "7d39ade34b69"


def upgrade():
    op.execute(CreateSequence(Sequence("annotation_id_seq")))
    op.add_column("annotation", sa.Column("pk", sa.Integer(), nullable=True))
    op.create_unique_constraint(op.f("uq__annotation__pk"), "annotation", ["pk"])


def downgrade():
    op.drop_constraint(op.f("uq__annotation__pk"), "annotation", type_="unique")
    op.drop_column("annotation", "pk")
    op.execute(DropSequence(Sequence("annotation_id_seq")))
