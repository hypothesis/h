# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from elasticsearch_dsl import connections
from h.search.client import get_client, get_client_old
from h.search.config import init
from h.search.core import Search
from h.search.core import FILTERS_KEY

__all__ = (
    'Search',
    'get_client',
    'init',
)


def includeme(config):
    settings = config.registry.settings
    settings.setdefault('es.host', 'http://localhost:9200')
    settings.setdefault('es.url', 'http://localhost:9201')
    settings.setdefault('es.index', 'hypothesis')

    # Allow users of this module to register additional search filter and
    # search matcher factories.
    config.registry[FILTERS_KEY] = []
    config.add_directive('add_search_filter',
                         lambda c, f: c.registry[FILTERS_KEY].append(config.maybe_dotted(f)))
    config.add_directive('get_search_filters',
                         lambda c: c.registry[FILTERS_KEY])

    # Add a property to all requests for easy access to the elasticsearch
    # client. This can be used for direct or bulk access without having to
    # reread the settings.
    config.registry['es.client'] = get_client_old(settings)
    config.add_request_method(
        lambda r: r.registry['es.client'],
        name='es',
        reify=True)
    # Set the elasticsearch client connection as the default connection.
    connections.add_connection('default', get_client(settings))
