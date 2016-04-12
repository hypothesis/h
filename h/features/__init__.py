# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import os

from pyramid import events
import transaction

from h.auth import role
from h.features import models

log = logging.getLogger(__name__)


class UnknownFeatureError(Exception):
    pass


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
        self._cache = {f.name: self._state(f) for f in models.Feature.all()}

    def enabled(self, name):
        """
        Determine if the named feature is enabled for the current request.

        If the feature has no override in the database, it will default to
        False. Features must be documented, and an UnknownFeatureError will be
        thrown if an undocumented feature is interrogated.

        When the internal cache is empty, it will automatically load the
        feature flags from the database first.
        """
        if not self._cache:
            self.load()

        if name not in self._cache:
            raise UnknownFeatureError(
                '{0} is not a valid feature name'.format(name))

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


@events.subscriber(events.ApplicationCreated)
def remove_old_flags_on_boot(event):
    """Remove old feature flags from the database on startup."""
    # Skip this if we're in a script, not actual app startup. See the comment
    # in h.script:main for an explanation.
    if 'H_SCRIPT' in os.environ:
        return

    models.Feature.remove_old_flags()
    transaction.commit()


def includeme(config):
    config.include('h.features.views')

    config.add_request_method(Client, name='feature', reify=True)
    config.add_route('features_status', '/app/features')

    config.scan(__name__)
