"""Add the user.edu_role_survey_* columns."""

from alembic import op
from sqlalchemy import CheckConstraint, Column, DateTime, UnicodeText

revision = "986ff45fcc23"
down_revision = "b6be2385d907"

RESPONSES = ["instructor", "not_instructor", "dismissed"]


def upgrade():
    op.add_column(
        "user",
        Column(
            "edu_role_survey_response",
            UnicodeText,
            CheckConstraint(
                " OR ".join(
                    f"edu_role_survey_response = '{response}'" for response in RESPONSES
                ),
                name="validate_edu_role_survey_response",
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "user",
        Column("edu_role_survey_responded_at", DateTime, nullable=True),
    )


def downgrade():
    op.drop_column("user", "edu_role_survey_responded_at")
    op.drop_column("user", "edu_role_survey_response")
