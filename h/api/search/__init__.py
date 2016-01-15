# -*- coding: utf-8 -*-

from h.api.search.client import Client
from h.api.search.core import search

__all__ = ('search',)


def _get_client(request):
    host = request.registry.settings['es.host']
    index = request.registry.settings['es.index']

    return Client(host, index)


def includeme(config):
    config.registry.settings.setdefault('es.host', 'http://localhost:9200')
    config.registry.settings.setdefault('es.index', 'annotator')

    # Add a property to all requests for easy access to the elasticsearch
    # client. This can be used for direct or bulk access without having to
    # reread the settings.
    config.add_request_method(_get_client, name='es', reify=True)
