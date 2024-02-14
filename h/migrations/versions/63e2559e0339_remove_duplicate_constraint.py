"""Remove duplicate constraint on document_uri."""

from alembic import op

revision = "63e2559e0339"
down_revision = "9e47da806421"


def upgrade():
    op.drop_constraint(
        "uq__document_uri__claimant_normalized", "document_uri", type_="unique"
    )


def downgrade():
    op.create_unique_constraint(
        "uq__document_uri__claimant_normalized",
        "document_uri",
        ["claimant_normalized", "uri_normalized", "type", "content_type"],
    )
