# -*- coding: utf-8 -*-
from pyramid.config import Configurator


def create_app(settings):
    config = Configurator(settings=settings)
    return config.make_wsgi_app()


def main(global_config, **settings):
    from . import config
    environ_config = config.settings_from_environment()
    settings.update(environ_config)  # from environment variables
    settings.update(global_config)   # from paste [DEFAULT] + command line
    return create_app(settings)
