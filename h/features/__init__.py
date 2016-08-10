# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from pyramid.events import NewRequest

from h import db
from h.features import client
from h.features import models

__all__ = ('Client',)

Client = client.Client


def _remove_old_flags_on_boot(event):
    """Remove old feature flags from the database on startup."""
    # Skip this if we're in a script, not actual app startup. See the comment
    # in h.cli:main for an explanation.
    if 'H_SCRIPT' in os.environ:
        return

    engine = db.make_engine(event.app.registry.settings)
    session = db.Session(bind=engine)
    models.Feature.remove_old_flags(session)
    session.commit()
    session.close()
    engine.dispose()


def includeme(config):
    config.include('h.features.views')

    config.add_request_method(Client, name='feature', reify=True)

    # Load the feature flags from the database at the beginning of each request.
    # This prevents sqlalchemy DetachedInstanceErrors that can occur if the
    # feature flags client tries to load the feature flags later on and the
    # database session has already been closed.
    # This is done on NewRequest to make sure that things like
    # request.effective_principals are already setup, so that we get the correct
    # feature flags.
    config.add_subscriber(lambda event: event.request.feature.load(),
                          NewRequest)

    config.add_subscriber(_remove_old_flags_on_boot,
                          'pyramid.events.ApplicationCreated')

    config.add_route('features_status', '/app/features')
