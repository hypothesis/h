"""
Make feature flag deletions cascade.

Revision ID: 74bff6a7d9de
Revises: 52a0b2e5a9c2
Create Date: 2017-08-01 09:59:51.200253
"""

from alembic import op

revision = "74bff6a7d9de"
down_revision = "52a0b2e5a9c2"

fk_name = "fk__featurecohort_feature__feature_id__feature"


def upgrade():
    op.drop_constraint(fk_name, "featurecohort_feature", type_="foreignkey")
    op.create_foreign_key(
        op.f(fk_name),
        "featurecohort_feature",
        "feature",
        ["feature_id"],
        ["id"],
        ondelete="cascade",
    )


def downgrade():
    op.drop_constraint(fk_name, "featurecohort_feature", type_="foreignkey")
    op.create_foreign_key(
        op.f(fk_name), "featurecohort_feature", "feature", ["feature_id"], ["id"]
    )
