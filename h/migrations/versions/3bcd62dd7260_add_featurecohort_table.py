"""
Add cohort table.

Revision ID: 3bcd62dd7260
Revises: dfa82518915a
Create Date: 2016-05-10 17:01:02.704596

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3bcd62dd7260"
down_revision = "dfa82518915a"


def upgrade():
    op.create_table(
        "featurecohort",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.UnicodeText(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "featurecohort_user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("cohort_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["cohort_id"], ["featurecohort.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("cohort_id", "user_id"),
    )


def downgrade():
    op.drop_table("featurecohort_user")
    op.drop_table("featurecohort")
