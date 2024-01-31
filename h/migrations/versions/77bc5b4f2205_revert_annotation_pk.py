"""Revert creation of annotation.pk."""

from alembic import op
from sqlalchemy.schema import CreateSequence, DropSequence, Sequence

revision = "77bc5b4f2205"
down_revision = "5d1abac3c1a1"


def upgrade():
    op.execute(DropSequence(Sequence("annotation_id_seq")))
    op.drop_constraint(op.f("uq__annotation__pk"), "annotation", type_="unique")
    op.drop_column("annotation", "pk")


def downgrade():
    """No downgrade, check version f064c2b2e04a."""
    pass
