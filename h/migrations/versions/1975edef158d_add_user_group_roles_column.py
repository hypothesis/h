"""Add the user_group.roles column."""

from alembic import op
from sqlalchemy import CheckConstraint, Column, text
from sqlalchemy.dialects.postgresql import JSONB

revision = "1975edef158d"
down_revision = "146179fa8d5e"


def upgrade():
    op.add_column(
        "user_group",
        Column(
            "roles",
            JSONB,
            CheckConstraint(
                " OR ".join(
                    f"""(roles = '["{role}"]'::jsonb)"""
                    for role in ["member", "moderator", "admin", "owner"]
                ),
                name="validate_role_strings",
            ),
            server_default=text("""'["member"]'::jsonb"""),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("user_group", "roles")
