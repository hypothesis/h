# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

import sqlalchemy as sa

from h.db import Base
from h.db import mixins

log = logging.getLogger(__name__)

FEATURES = {
    'activity_pages': "Show the new activity pages?",
    'selection_tabs': "Show the tabs to select between annotations and notes?",
    'orphans_tab': "Show the orphans tab to separate anchored and unanchored annotations?",
}

# Once a feature has been fully deployed, we remove the flag from the codebase.
# We can't do this in one step, because removing it entirely will cause stage
# to remove the flag data from the database on boot, which will in turn disable
# the feature in prod.
#
# Instead, the procedure for removing a feature is as follows:
#
# 1. Remove all feature lookups for the named feature throughout the code.
#
# 2. Move the feature to FEATURES_PENDING_REMOVAL. This ensures that the
#    feature won't show up in the admin panel, and any uses of the feature will
#    provoke UnknownFeatureErrors (server-side) or console warnings
#    (client-side).
#
# 3. Deploy these changes all the way out to production.
#
# 4. Finally, remove the feature from FEATURES_PENDING_REMOVAL.
#
FEATURES_PENDING_REMOVAL = {}


class Feature(Base):

    """A feature flag for the application."""

    __tablename__ = 'feature'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)

    # Is the feature enabled for everyone?
    everyone = sa.Column(sa.Boolean,
                         nullable=False,
                         default=False,
                         server_default=sa.sql.expression.false())

    # Is the feature enabled for admins?
    admins = sa.Column(sa.Boolean,
                       nullable=False,
                       default=False,
                       server_default=sa.sql.expression.false())

    # Is the feature enabled for all staff?
    staff = sa.Column(sa.Boolean,
                      nullable=False,
                      default=False,
                      server_default=sa.sql.expression.false())

    @property
    def description(self):
        return FEATURES[self.name]

    @classmethod
    def all(cls, session):
        """Fetch (or, if necessary, create) rows for all defined features."""
        results = []
        for name in FEATURES:
            feat = session.query(cls).filter(cls.name == name).first()
            if feat is None:
                feat = cls(name=name)
                session.add(feat)
            results.append(feat)
        return results

    @classmethod
    def remove_old_flags(cls, session):
        """
        Remove old/unknown data from the feature table.

        When a feature flag is removed from the codebase, it will remain in the
        database. This could potentially cause very surprising issues in the
        event that a feature flag with the same name (but a different meaning)
        is added at some point in the future.

        This function removes unknown feature flags from the database.
        """
        # N.B. We remove only those features we know absolutely nothing about,
        # which means that FEATURES_PENDING_REMOVAL are left alone.
        known = set(FEATURES) | set(FEATURES_PENDING_REMOVAL)
        unknown_flags = session.query(cls).filter(sa.not_(cls.name.in_(known)))
        count = unknown_flags.delete(synchronize_session=False)
        if count > 0:
            log.info('removed %d old/unknown feature flags from database', count)

    def __repr__(self):
        return '<Feature {f.name} everyone={f.everyone}>'.format(f=self)


class FeatureCohort(Base, mixins.Timestamps):
    __tablename__ = 'featurecohort'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.UnicodeText(), nullable=False, index=True)

    # Cohort membership
    members = sa.orm.relationship('User',
                                  secondary='featurecohort_user',
                                  backref='cohorts')

    features = sa.orm.relationship('Feature',
                                   secondary='featurecohort_feature',
                                   backref='cohorts')

    def __init__(self, name):
        self.name = name


FEATURECOHORT_USER_TABLE = sa.Table(
    'featurecohort_user', Base.metadata,
    sa.Column('id',
              sa.Integer,
              nullable=False,
              autoincrement=True,
              primary_key=True),
    sa.Column('cohort_id',
              sa.Integer,
              sa.ForeignKey('featurecohort.id'),
              nullable=False),
    sa.Column('user_id',
              sa.Integer,
              sa.ForeignKey('user.id'),
              nullable=False),
    sa.UniqueConstraint('cohort_id', 'user_id'),
)

FEATURECOHORT_FEATURE_TABLE = sa.Table(
    'featurecohort_feature', Base.metadata,
    sa.Column('id',
              sa.Integer(),
              nullable=False,
              autoincrement=True,
              primary_key=True),
    sa.Column('cohort_id',
              sa.Integer(),
              sa.ForeignKey('featurecohort.id'),
              nullable=False),
    sa.Column('feature_id',
              sa.Integer(),
              sa.ForeignKey('feature.id'),
              nullable=False),
    sa.UniqueConstraint('cohort_id', 'feature_id'),
)
