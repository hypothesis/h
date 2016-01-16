# -*- coding: utf-8 -*-

from pyramid.settings import asbool

from h.api.search.client import Client
from h.api.search.config import configure_index
from h.api.search.core import search

__all__ = ('search',)


def _get_client(settings):
    host = settings['es.host']
    index = settings['es.index']

    return Client(host, index)


def includeme(config):
    settings = config.registry.settings
    settings.setdefault('es.host', 'http://localhost:9200')
    settings.setdefault('es.index', 'annotator')

    # Add a property to all requests for easy access to the elasticsearch
    # client. This can be used for direct or bulk access without having to
    # reread the settings.
    config.add_request_method(lambda r: _get_client(r.registry.settings),
                              name='es',
                              reify=True)

    # If requested, automatically configure the index
    if asbool(settings.get('h.search.autoconfig', False)):
        client = _get_client(settings)
        configure_index(client)
