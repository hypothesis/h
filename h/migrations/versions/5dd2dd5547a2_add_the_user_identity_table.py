"""Add the user_identity table."""
import sqlalchemy as sa
from alembic import op

revision = "5dd2dd5547a2"
down_revision = "178270e3ee58"


def upgrade():
    op.create_table(
        "user_identity",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("provider", sa.UnicodeText(), nullable=False),
        sa.Column("provider_unique_id", sa.UnicodeText(), nullable=False),
        sa.UniqueConstraint("provider", "provider_unique_id"),
    )


def downgrade():
    op.drop_table("user_identity")
