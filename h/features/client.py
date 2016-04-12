# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.auth import role
from h.features import models


class UnknownFeatureError(Exception):
    pass


class Client(object):
    """
    Determine if the named feature is enabled for the current request.
    If the feature has no override in the database, it will default to
    False. Features must be documented, and an UnknownFeatureError will be
    thrown if an undocumented feature is interrogated.
    """

    def __init__(self, request, fetcher=models.Feature.all):
        self.request = request
        self._fetcher = fetcher
        self._cache = None

    def __call__(self, name):
        return self.enabled(name)

    def enabled(self, name):
        """
        Determine if the named feature is enabled for the current request.

        If the feature has no override in the database, it will default to
        False. Features must be documented, and an UnknownFeatureError will be
        thrown if an undocumented feature is interrogated.

        When the internal cache is empty, it will automatically load the
        feature flags from the database first.
        """
        if self._cache is None:
            self._load()

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
        if self._cache is None:
            self._load()

        return self._cache

    def clear(self):
        self._cache = None

    def _load(self):
        """Loads the feature flag states into the internal cache."""
        self._cache = {f.name: self._state(f) for f in self._fetcher()}

    def _state(self, feature):
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
