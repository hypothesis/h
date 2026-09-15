"""Create the user_survey_response table."""

import sqlalchemy as sa
from alembic import op

revision = "2fdc26d19dbc"
down_revision = "b6be2385d907"

RESPONSES = ["instructor", "not_instructor", "dismissed"]


def upgrade() -> None:
    op.create_table(
        "user_survey_response",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("survey", sa.UnicodeText(), nullable=False),
        sa.Column("response", sa.UnicodeText(), nullable=False),
        sa.Column("responded_at", sa.DateTime(), nullable=False),
        sa.Column("hubspot_synced_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__user_survey_response__user_id__user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__user_survey_response")),
        sa.UniqueConstraint(
            "user_id",
            "survey",
            name=op.f("uq__user_survey_response__user_id__survey"),
        ),
        sa.CheckConstraint(
            "survey = 'edu_role' AND response IN ("
            + ", ".join(f"'{response}'" for response in RESPONSES)
            + ")",
            name=op.f("ck__user_survey_response__validate_response"),
        ),
    )


def downgrade() -> None:
    op.drop_table("user_survey_response")
