# -*- coding: utf-8 -*-
import os

from pyramid.tweens import EXCVIEW
from raven.base import Client


def raven_tween_factory(handler, registry):
    client = Client()

    def raven_tween(request):
        try:
            return handler(request)
        except Exception:
            client.captureException()
            raise

    return raven_tween


def includeme(config):
    if 'SENTRY_DSN' in os.environ:
        config.add_tween('h.tweens.raven_tween_factory', under=EXCVIEW)
