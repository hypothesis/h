# -*- coding: utf-8 -*-
"""OAuth integration support."""
from .interfaces import IClient, IClientFactory
from .lib import get_client, set_client_factory
from .tokens import AnnotatorToken

__all__ = [
    'AnnotatorToken',
    'IClient',
    'IClientFactory',
]


def includeme(config):
    config.include('pyramid_oauthlib')
    config.add_directive('set_client_factory', set_client_factory)
    config.add_request_method(name='get_client', callable=get_client)
