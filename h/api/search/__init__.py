# -*- coding: utf-8 -*-

from pyramid.settings import asbool

from h.api.search.client import Client
from h.api.search.config import configure_index
from h.api.search.core import search
from h.api.search.core import FILTERS_KEY
from h.api.search.core import MATCHERS_KEY

__all__ = ('search',)


def _get_client(settings):
    """Return a client for the Elasticsearch index."""
    host = settings['es.host']
    index = settings['es.index']
    kwargs = {}
    kwargs['timeout'] = settings.get('es.client_timeout', 10)

    if 'es.client_poolsize' in settings:
        kwargs['maxsize'] = settings['es.client_poolsize']

    return Client(host, index, **kwargs)


def _legacy_get_client(settings):
    """Return a client for the legacy Elasticsearch index."""
    host = settings['es.host']
    index = settings['legacy.es.index']
    kwargs = {}
    kwargs['timeout'] = settings.get('es.client_timeout', 10)

    if 'es.client_poolsize' in settings:
        kwargs['maxsize'] = settings['es.client_poolsize']

    return Client(host, index, **kwargs)


def includeme(config):
    settings = config.registry.settings
    settings.setdefault('es.host', 'http://localhost:9200')
    settings.setdefault('es.index', 'hypothesis')
    settings.setdefault('legacy.es.index', 'annotator')

    # Allow users of this module to register additional search filter and
    # search matcher factories.
    config.registry[FILTERS_KEY] = []
    config.registry[MATCHERS_KEY] = []
    config.add_directive('add_search_filter',
                         lambda c, f: c.registry[FILTERS_KEY].append(f))
    config.add_directive('add_search_matcher',
                         lambda c, m: c.registry[MATCHERS_KEY].append(m))

    # Add a property to all requests for easy access to the elasticsearch
    # client. This can be used for direct or bulk access without having to
    # reread the settings.
    config.add_request_method(
        lambda r: _get_client(r.registry.settings),
        name='es',
        reify=True)

    # request.legacy_es is always a client for the legacy Elasticsearch index,
    # regardless of whether the 'postgres' feature flag is on.
    # This should be used to write to the legacy search index.
    # TODO: Remove when postgres migration is done
    config.add_request_method(
        lambda r: _legacy_get_client(r.registry.settings),
        name='legacy_es',
        reify=True)

    # request.new_es is always a client for the legacy Elasticsearch index,
    # regardless of whether the 'postgres' feature flag is on.
    # This should be used to write to the new search index.
    # TODO: Remove when postgres migration is done
    config.add_request_method(
        lambda r: _get_client(r.registry.settings),
        name='new_es',
        reify=True)

    # If requested, automatically configure the index
    if asbool(settings.get('h.search.autoconfig', False)):
        configure_index(_get_client(settings))
        configure_index(_legacy_get_client(settings))
