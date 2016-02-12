# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import os

from pyramid import events
from pyramid.view import view_config
import sqlalchemy as sa
import transaction

from h.db import Base

log = logging.getLogger(__name__)

FEATURES = {
    'claim': "Enable 'claim your username' web views?",
    'new_homepage': "Show the new homepage design?",
    'truncate_annotations': "Truncate long quotes and bodies in annotations?",
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
    'embed_media': "Replace YouTube, Vimeo etc links in annotations with embeds",
    'sidebar_tutorial': "Show a tutorial to new users in the sidebar",
}


class UnknownFeatureError(Exception):
    pass


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


def flag_enabled(request, name):
    """
    Determine if the named feature is enabled for the current request.

    If the feature has no override in the database, it will default to False.
    Features must be documented, and an UnknownFeatureError will be thrown if
    an undocumented feature is interrogated.
    """
    if name not in FEATURES:
        raise UnknownFeatureError(
            '{0} is not a valid feature name'.format(name))

    feat = Feature.get_by_name(name)

    # Features that don't exist in the database are off.
    if feat is None:
        return False
    # Features that are on for everyone are on.
    if feat.everyone:
        return True
    # Features that are on for admin are on if the current user is an admin.
    if feat.admins and 'group:__admin__' in request.effective_principals:
        return True
    # Features that are on for staff are on if the current user is a staff
    # member.
    if feat.staff and 'group:__staff__' in request.effective_principals:
        return True
    return False


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
    transaction.commit()


@events.subscriber(events.ApplicationCreated)
def remove_old_flags_on_boot(event):
    """Remove old feature flags from the database on startup."""
    # Skip this if we're in a script, not actual app startup. See the comment
    # in h.script:main for an explanation.
    if 'H_SCRIPT' in os.environ:
        return

    remove_old_flags()


def all(request):
    """
    Returns a dict mapping feature flag names to enabled states
    for the user associated with a given request.
    """
    return {k: flag_enabled(request, k) for k in FEATURES.keys()}


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
    return all(request)


def includeme(config):
    config.add_request_method(flag_enabled, name='feature')
    config.add_route('features_status', '/app/features')
    config.scan(__name__)
