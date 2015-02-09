# -*- coding: utf-8 -*-
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from .app import main
__all__ = ['main']


def includeme(config):
    config.include('h.authentication')
    config.include('h.authorization')
    config.include('h.errors')
    config.include('h.features')
    config.include('h.queue')
    config.include('h.subscribers')
    config.include('h.views')

    if config.registry.feature('api'):
        config.include('h.api')

    if config.registry.feature('streamer'):
        config.include('h.streamer')

    if config.registry.feature('notification'):
        config.include('h.notification')

    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('.js')
    config.add_jinja2_renderer('.txt')
    config.add_jinja2_renderer('.html')
