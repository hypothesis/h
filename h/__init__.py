# -*- coding: utf-8 -*-
from pyramid.path import AssetResolver
from pyramid.response import FileResponse

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from .app import main
__all__ = [main]


def includeme(config):
    config.include('pyramid_jinja2')
    config.include('pyramid_multiauth')
    config.include('h.api')
    config.include('h.features')
    config.include('h.queue')
    config.include('h.subscribers')
    config.include('h.views')

    if config.registry.feature('streamer'):
        config.include('h.streamer')

    config.set_root_factory('h.resources.RootFactory')

    config.add_jinja2_renderer('.js')
    config.add_jinja2_renderer('.txt')
    config.add_jinja2_renderer('.html')

    favicon = AssetResolver().resolve('h:favicon.ico')
    config.add_route('favicon', '/favicon.ico')
    config.add_view(
        lambda request: FileResponse(favicon.abspath(), request=request),
        route_name='favicon'
    )

    config.add_route('ok', '/ruok')
    config.add_view(lambda request: 'imok', renderer='string', route_name='ok')
