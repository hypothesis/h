# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import os

from pyramid import events
from pyramid.view import view_config
import sqlalchemy as sa
import transaction

from h import db
from h.auth import role

log = logging.getLogger(__name__)

FEATURES = {
    'direct_linking': "Generate direct links to annotations in context in the client?",
    'new_homepage': "Show the new homepage design?",
    'postgres_read': 'Use postgres to fetch annotations from storage',
    'postgres_write': 'Send annotation CRUDs to <em>both</em> Postgres and the old '
                      'Elasticsearch index',
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
FEATURES_PENDING_REMOVAL = {
    'claim': "Enable 'claim your username' web views?",
    'ops_disable_streamer_uri_equivalence': "[Ops] Disable streamer URI equivalence support?",
}


class UnknownFeatureError(Exception):
    pass


class Feature(db.Base):

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
    def all(cls):
        """Fetch (or, if necessary, create) rows for all defined features."""
        results = []
        for name in FEATURES:
            feat = cls.get_by_name(name)
            if feat is None:
                feat = cls(name=name)
                cls.query.session.add(feat)
            results.append(feat)
        return results

    @classmethod
    def get_by_name(cls, name):
        """Fetch a flag by name."""
        return cls.query.filter(cls.name == name).first()

    def __repr__(self):
        return '<Feature {f.name} everyone={f.everyone}>'.format(f=self)


class Client(object):
    """
    Determine if the named feature is enabled for the current request.
    If the feature has no override in the database, it will default to
    False. Features must be documented, and an UnknownFeatureError will be
    thrown if an undocumented feature is interrogated.
    """

    def __init__(self, request):
        self.request = request
        self._cache = {}

    def __call__(self, name):
        return self.enabled(name)

    def load(self):
        """Loads the feature flag states into the internal cache."""
        all_ = self._fetch_features()
        features = {f.name: f for f in all_}
        self._cache = {n: self._state(features.get(n))
                       for n in FEATURES.keys()}

    def enabled(self, name):
        """
        Determine if the named feature is enabled for the current request.

        If the feature has no override in the database, it will default to
        False. Features must be documented, and an UnknownFeatureError will be
        thrown if an undocumented feature is interrogated.

        When the internal cache is empty, it will automatically load the
        feature flags from the database first.
        """
        if name not in FEATURES:
            raise UnknownFeatureError(
                '{0} is not a valid feature name'.format(name))

        if not self._cache:
            self.load()

        return self._cache[name]

    def all(self):
        """
        Returns a dict mapping feature flag names to enabled states
        for the user associated with a given request.

        When the internal cache is empty, it will automatically load the
        feature flags from the database first.
        """
        if not self._cache:
            self.load()

        return self._cache

    def clear(self):
        self._cache = {}

    def _state(self, feature):
        # Features that don't exist in the database are off.
        if feature is None:
            return False
        # Features that are on for everyone are on.
        if feature.everyone:
            return True
        # Features that are on for admin are on if the current user is an
        # admin.
        if feature.admins and role.Admin in self.request.effective_principals:
            return True
        # Features that are on for staff are on if the current user is a staff
        # member.
        if feature.staff and role.Staff in self.request.effective_principals:
            return True
        return False

    def _fetch_features(self):
        return self.request.db.query(Feature).filter(
                Feature.name.in_(FEATURES.keys())).all()


def remove_old_flags():
    """
    Remove old/unknown data from the feature table.

    When a feature flag is removed from the codebase, it will remain in the
    database. This could potentially cause very surprising issues in the event
    that a feature flag with the same name (but a different meaning) is added
    at some point in the future.

    This function removes unknown feature flags from the database, and is run
    once at application startup.
    """
    # N.B. We remove only those features we know absolutely nothing about,
    # which means that FEATURES_PENDING_REMOVAL are left alone.
    known = set(FEATURES) | set(FEATURES_PENDING_REMOVAL)
    unknown_flags = Feature.query.filter(sa.not_(Feature.name.in_(known)))
    count = unknown_flags.delete(synchronize_session=False)
    if count > 0:
        log.info('removed %d old/unknown feature flags from database', count)


@events.subscriber(events.ApplicationCreated)
def remove_old_flags_on_boot(event):
    """Remove old feature flags from the database on startup."""
    # Skip this if we're in a script, not actual app startup. See the comment
    # in h.script:main for an explanation.
    if 'H_SCRIPT' in os.environ:
        return

    remove_old_flags()
    transaction.commit()


# Deprecated dedicated endpoint for feature flag data,
# kept for compatibility with older clients (<= 0.8.6).
# Newer clients get feature flag data as part of the session data
# from the /app endpoint.
@view_config(route_name='features_status',
             request_method='GET',
             accept='application/json',
             renderer='json',
             http_cache=(0, {'no_store': False}))
def features_status(request):
    return request.feature.all()


def includeme(config):
    config.add_request_method(Client, name='feature', reify=True)
    config.add_route('features_status', '/app/features')
    config.scan(__name__)
