# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from h import db
from h.models import Feature


def remove_old_flags(event):
    """Remove old feature flags from the database."""
    # Skip this if we're in a script, not actual app startup. See the comment
    # in h.cli:main for an explanation.
    if 'H_SCRIPT' in os.environ:
        return

    engine = db.make_engine(event.app.registry.settings)
    session = db.Session(bind=engine)
    Feature.remove_old_flags(session)
    session.commit()
    session.close()
    engine.dispose()


def preload_flags(event):
    """Load all feature flags from the database for this request."""
    if event.request.path.startswith(('/assets/', '/_debug_toolbar/')):
        return
    # This prevents sqlalchemy DetachedInstanceErrors that can occur if the
    # feature flags client tries to load the feature flags later on and the
    # database session has already been closed.
    event.request.feature.load()
