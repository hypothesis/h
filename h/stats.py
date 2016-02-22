# -*- coding: utf-8 -*-
import statsd

__all__ = ('get_client',)


def get_client(settings):
    conn = statsd.Connection(host=settings.get('statsd.host'),
                             port=settings.get('statsd.port'))
    return statsd.Client(__package__, connection=conn)


def includeme(config):
    # Allow easy access to a statsd client as `request.stats`
    config.add_request_method(lambda r: get_client(r.registry.settings),
                              name='stats',
                              reify=True)
