#!/usr/bin/env python

routes = [
    ('home', '/'),

    ('store', '/api/*subpath'),
    ('token', '/token'),

    ('bookmarklet', '/bookmarklet.js')
]

def create_app(config):
    config.include('.assets')
    config.include('.models')
    config.include('.views')

    for view, path in routes:
        config.add_route(view, path)

    return config.make_wsgi_app()
