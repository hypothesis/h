# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from h.search_old.client import get_client
from h.search_old.config import init
from h.search_old.core import Search
from h.search_old.core import FILTERS_KEY

__all__ = (
    'Search',
    'get_client',
    'init',
)


def includeme(config):
    settings = config.registry.settings
    settings.setdefault('es.host', 'http://localhost:9200')
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
    config.registry['es.client'] = get_client(settings)
    config.add_request_method(
        lambda r: r.registry['es.client'],
        name='es',
        reify=True)
