#!/usr/bin/env python
from pyramid.decorator import reify
from pyramid.request import Request

class HypothesisRequest(Request):
    @reify
    def db(self):
        self.registry.settings['db.session_factory']()

routes = [
    ('home', '/')
]

def create_app(config):
    config.set_request_factory(HypothesisRequest)

    config.include('hypothesis.views')
    config.include('hypothesis.models')
    config.include('hypothesis.assets')

    for view, path in routes:
        config.add_route(view, path)

    return config.make_wsgi_app()
