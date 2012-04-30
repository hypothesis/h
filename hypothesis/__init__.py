#!/usr/bin/env python
from pyramid.config import Configurator

def includeme(config):
    config.include('.api')
    config.include('.models')
    config.include('.resources')
    config.include('.views')

def create_app(settings):
    config = Configurator(settings=settings)
    config.include('.')
    return config.make_wsgi_app()

def main(global_config, **settings):
    return create_app(settings)
