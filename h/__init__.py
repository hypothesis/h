# -*- coding: utf-8 -*-
"""Initialize configuration."""

from .app import main
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

__all__ = ['main']


def includeme(config):
    """Include config sections and setup Jinja."""
    config.include('h.authentication')
    config.include('h.authorization')
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
