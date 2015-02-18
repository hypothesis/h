# -*- coding: utf-8 -*-
"""The main h application."""
from pyramid.config import Configurator
from pyramid.path import AssetResolver
from pyramid.response import FileResponse


def create_app(settings):
    """Configure and add static routes and views. Return the WSGI app."""
    config = Configurator(settings=settings)
    config.include('h')

    favicon = AssetResolver().resolve('h:favicon.ico')
    config.add_route('favicon', '/favicon.ico')
    config.add_view(
        lambda request: FileResponse(favicon.abspath(), request=request),
        route_name='favicon'
    )

    config.add_route('ok', '/ruok')
    config.add_view(lambda request: 'imok', renderer='string', route_name='ok')

    config.set_root_factory('h.resources.RootFactory')

    return config.make_wsgi_app()


def main(global_config, **settings):
    """Create the h application with all the awesomeness that is configured."""
    from h import config
    environ_config = config.settings_from_environment()
    settings.update(environ_config)  # from environment variables
    settings.update(global_config)   # from paste [DEFAULT] + command line
    return create_app(settings)
