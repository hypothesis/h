# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

import sqlalchemy as sa

from h.db import Base

log = logging.getLogger(__name__)

FEATURES = {
    'activity_pages': "Show the new activity pages?",
    'defer_realtime_updates': ("Require a user action before applying real-time"
                               " updates to annotations in the client?"),
    'orphans_tab': "Show the orphans tab to separate anchored and unanchored annotations?",
    'search_page': "Show the activity pages search skeleton page?",
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
        features = {f.name: f
                    for f in session.query(cls)
                    if f.name in FEATURES}

        # Add missing features
        missing = [cls(name=n)
                   for n in FEATURES
                   if n not in features]
        session.add_all(missing)

        return list(features.values()) + missing

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
