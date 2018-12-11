# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import statsd

__all__ = ("get_client",)


def get_client(settings):
    return statsd.StatsClient(
        host=settings.get("statsd.host", "localhost"),
        port=settings.get("statsd.port", 8125),
        prefix=settings.get("statsd.prefix", ""),
    )


def includeme(config):
    # Allow easy access to a statsd client as `request.stats`
    config.add_request_method(
        lambda r: get_client(r.registry.settings), name="stats", reify=True
    )
