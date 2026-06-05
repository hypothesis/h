"""Add the user_group.lms_role column."""

from alembic import op
from sqlalchemy import CheckConstraint, Column, UnicodeText

revision = "b6be2385d907"
down_revision = "3794945d8e88"


def upgrade():
    op.add_column(
        "user_group",
        Column(
            "lms_role",
            UnicodeText,
            CheckConstraint(
                " OR ".join(
                    f"lms_role = '{role}'" for role in ["lms_instructor", "lms_student"]
                ),
                name="validate_lms_role",
            ),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("user_group", "lms_role")
