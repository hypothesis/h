# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from h.search.client import get_client
from h.search.config import init
from h.search.connection import connect
from h.search.core import Search
from h.search.query import TopLevelAnnotationsFilter
from h.search.query import AuthorityFilter
from h.search.query import TagsAggregation
from h.search.query import UsersAggregation

__all__ = (
    'Search',
    'TopLevelAnnotationsFilter',
    'AuthorityFilter',
    'TagsAggregation',
    'UsersAggregation',
    'get_client',
    'init',
    'connect'
)


def includeme(config):
    settings = config.registry.settings

    # Connection to version 6.x of ES follows
    # TODO The munging of these settings may change when settings refactoring complete
    kwargs = {}
    kwargs['max_retries'] = settings.get('es.client.max_retries', 3)
    kwargs['retry_on_timeout'] = settings.get('es.client.retry_on_timeout', False)
    kwargs['timeout'] = settings.get('es.client.timeout', 10)

    if 'es.client_poolsize' in settings:
        kwargs['maxsize'] = settings['es.client_poolsize']

    # TODO should pass `hosts` param once that setting (ELASTICSEARCH_URL) is in place
    connect(**kwargs)

    # Connection to old (ES1.5) follows
    settings.setdefault('es.host', 'http://localhost:9200')
    settings.setdefault('es.index', 'hypothesis')

    # Add a property to all requests for easy access to the elasticsearch
    # client. This can be used for direct or bulk access without having to
    # reread the settings.
    config.registry['es.client'] = get_client(settings)
    config.add_request_method(
        lambda r: r.registry['es.client'],
        name='es',
        reify=True)

    connect()
