# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

import transaction

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

    # FIXME: This function should create its own transient session rather than
    # relying on a scoped session.
    from h.db import Session
    models.Feature.remove_old_flags(Session)
    transaction.commit()


def includeme(config):
    config.include('h.features.views')

    config.add_request_method(Client, name='feature', reify=True)
    config.add_subscriber(_remove_old_flags_on_boot,
                          'pyramid.events.ApplicationCreated')

    config.add_route('features_status', '/app/features')
