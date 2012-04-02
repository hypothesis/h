#!/usr/bin/env python
from pyramid.config import Configurator
from pyramid.paster import bootstrap

def includeme(config):
    config.include('.api')
    config.include('.models')
    config.include('.resources')
    config.include('.views')

def create_app(settings):
    config = Configurator(settings=settings)
    config.include('.')
    return config.make_wsgi_app()

def main(context, **settings):
    return create_app(settings)
