"""Add annotation.pk"""
import sqlalchemy as sa
from sqlalchemy.schema import Sequence, CreateSequence, DropSequence
from alembic import op

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
