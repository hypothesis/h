# -*- coding: utf-8 -*-
import statsd

__all__ = ('get_client',)


def get_client(settings):
    return statsd.StatsClient(host=settings.get('statsd.host'),
                              port=settings.get('statsd.port'))


def includeme(config):
    config.registry.settings.setdefault('statsd.host', 'localhost')
    config.registry.settings.setdefault('statsd.port', 8125)

    # Allow easy access to a statsd client as `request.stats`
    config.add_request_method(lambda r: get_client(r.registry.settings),
                              name='stats',
                              reify=True)
