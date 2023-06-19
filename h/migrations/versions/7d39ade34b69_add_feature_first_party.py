"""Add feature.first_party column."""
import sqlalchemy as sa
from alembic import op

revision = "7d39ade34b69"
down_revision = "be612e693243"


def upgrade():
    op.add_column(
        "feature",
        sa.Column(
            "first_party",
            sa.Boolean,
            nullable=False,
            server_default=sa.sql.expression.false(),
        ),
    )


def downgrade():
    op.drop_column("feature", "first_party")
