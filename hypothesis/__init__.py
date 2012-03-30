#!/usr/bin/env python
from os import environ
from os.path import join
"""
If a virtual environment is active, make sure it's being used.
Globally-installed console scripts use an absolute shebang path which
prevents them from importing virtualenv packages. Detect that case here
and correct for it.
"""
try:
    activate = join(environ['VIRTUAL_ENV'], 'bin', 'activate_this.py')
    execfile(activate, dict(__file__=activate))
except KeyError:
    pass

from pyramid.config import Configurator
from pyramid.paster import bootstrap, setup_logging


routes = [
    ('home', '/'),

    ('api', '/api/*subpath'),
    ('token', '/token'),

    ('bookmarklet', '/bookmarklet.js')
]

def create_app(fname):
    env = bootstrap('development.ini')
    setup_logging('development.ini')
    env['closer']()
    return env['app']

def main(context, **settings):
    config = Configurator(settings=settings)
    config.include('.')

    for view, path in routes:
        config.add_route(view, path)

    return config.make_wsgi_app()

def includeme(config):
    config.include('.api')
    config.include('.assets')
    config.include('.models')
    config.include('.views')
