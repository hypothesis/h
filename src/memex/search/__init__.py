# -*- coding: utf-8 -*-

from pyramid.settings import asbool

from memex.search.client import Client
from memex.search.config import init
from memex.search.core import Search
from memex.search.core import FILTERS_KEY
from memex.search.core import MATCHERS_KEY

__all__ = ('Search',)


def _get_client(settings):
    """Return a client for the Elasticsearch index."""
    host = settings['es.host']
    index = settings['es.index']
    kwargs = {}
    kwargs['max_retries'] = settings.get('es.client.max_retries', 3)
    kwargs['retry_on_timeout'] = settings.get('es.client.retry_on_timeout', False)
    kwargs['timeout'] = settings.get('es.client.timeout', 10)

    if 'es.client_poolsize' in settings:
        kwargs['maxsize'] = settings['es.client_poolsize']

    return Client(host, index, **kwargs)


def includeme(config):
    settings = config.registry.settings
    settings.setdefault('es.host', 'http://localhost:9200')
    settings.setdefault('es.index', 'hypothesis')

    # Allow users of this module to register additional search filter and
    # search matcher factories.
    config.registry[FILTERS_KEY] = []
    config.registry[MATCHERS_KEY] = []
    config.add_directive('memex_add_search_filter',
                         lambda c, f: c.registry[FILTERS_KEY].append(f))
    config.add_directive('memex_add_search_matcher',
                         lambda c, m: c.registry[MATCHERS_KEY].append(m))

    # Add a property to all requests for easy access to the elasticsearch
    # client. This can be used for direct or bulk access without having to
    # reread the settings.
    config.registry['es.client'] = client = _get_client(settings)
    config.add_request_method(
        lambda r: r.registry['es.client'],
        name='es',
        reify=True)

    config.action('memex.search.init', init, args=(client,), order=10)
