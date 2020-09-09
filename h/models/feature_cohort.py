import sqlalchemy as sa

from h.db import Base, mixins


class FeatureCohort(Base, mixins.Timestamps):
    __tablename__ = "featurecohort"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.UnicodeText(), nullable=False, index=True)

    # Cohort membership
    members = sa.orm.relationship(
        "User", secondary="featurecohort_user", backref="cohorts"
    )

    features = sa.orm.relationship(
        "Feature", secondary="featurecohort_feature", backref="cohorts"
    )

    def __init__(self, name):
        self.name = name


FEATURECOHORT_USER_TABLE = sa.Table(
    "featurecohort_user",
    Base.metadata,
    sa.Column("id", sa.Integer, nullable=False, autoincrement=True, primary_key=True),
    sa.Column(
        "cohort_id", sa.Integer, sa.ForeignKey("featurecohort.id"), nullable=False
    ),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False),
    sa.UniqueConstraint("cohort_id", "user_id"),
)

FEATURECOHORT_FEATURE_TABLE = sa.Table(
    "featurecohort_feature",
    Base.metadata,
    sa.Column("id", sa.Integer(), nullable=False, autoincrement=True, primary_key=True),
    sa.Column(
        "cohort_id", sa.Integer(), sa.ForeignKey("featurecohort.id"), nullable=False
    ),
    sa.Column(
        "feature_id",
        sa.Integer(),
        sa.ForeignKey("feature.id", ondelete="cascade"),
        nullable=False,
    ),
    sa.UniqueConstraint("cohort_id", "feature_id"),
)
