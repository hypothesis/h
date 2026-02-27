"""Add user.youtube_gdpr_banner_dismissed column."""

import sqlalchemy as sa
from alembic import op

revision = "1d93a1310f5d"
down_revision = "7c1a3e2b9f20"


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "youtube_gdpr_banner_dismissed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.expression.false(),
        ),
    )


def downgrade():
    op.drop_column("user", "youtube_gdpr_banner_dismissed")
