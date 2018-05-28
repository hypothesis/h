# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from h.search.client import get_client
from h.search.config import init
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
)


def includeme(config):
    settings = config.registry.settings
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
