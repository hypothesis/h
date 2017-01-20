# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def preload_flags(event):
    """Load all feature flags from the database for this request."""
    if event.request.path.startswith(('/assets/', '/_debug_toolbar/')):
        return
    # This prevents sqlalchemy DetachedInstanceErrors that can occur if the
    # feature flags client tries to load the feature flags later on and the
    # database session has already been closed.
    event.request.feature.load()
