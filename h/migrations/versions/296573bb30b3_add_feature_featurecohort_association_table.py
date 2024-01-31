"""
Add feature_featurecohort association table.

Revision ID: 296573bb30b3
Revises: f6ffcfc50583
Create Date: 2016-06-09 16:35:09.065224

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "296573bb30b3"
down_revision = "f6ffcfc50583"


def upgrade():
    op.create_table(
        "featurecohort_feature",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("feature_id", sa.Integer(), nullable=False),
        sa.Column("cohort_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["cohort_id"], ["featurecohort.id"]),
        sa.ForeignKeyConstraint(["feature_id"], ["feature.id"]),
        sa.UniqueConstraint("cohort_id", "feature_id"),
    )


def downgrade():
    op.drop_table("featurecohort_feature")
