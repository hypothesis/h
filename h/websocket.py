# -*- coding: utf-8 -*-
"""
The websocket server for Hypothesis.

This file contains a worker class for Gunicorn (:py:class:`h.websocket.Worker`)
and a stripped-down Pyramid application which exposes a single endpoint for
serving the "streamer" over the websocket.
"""

from gunicorn.workers.ggevent import GeventPyWSGIWorker
from gunicorn.workers.ggevent import PyWSGIHandler
from pyramid.config import Configurator
from ws4py.server.geventserver import WSGIServer
from ws4py.server.geventserver import WebSocketWSGIHandler

from h import features
from h.app import get_settings


class WSGIHandler(PyWSGIHandler, WebSocketWSGIHandler):
    def finalize_headers(self):
        if self.environ.get('HTTP_UPGRADE', '').lower() == 'websocket':
            # Middleware, like Raven, may yield from the empty upgrade
            # response, confusing this method into sending "Transfer-Encoding:
            # chunked" and, in turn, this confuses some strict WebSocket
            # clients.
            if not hasattr(self.result, '__len__'):
                self.result = list(self.result)

            # ws4py 0.3.4 will try to pop the websocket from the environ
            # even if it doesn't exist, causing a key error.
            self.environ.setdefault('ws4py.websocket', None)

        super(WSGIHandler, self).finalize_headers()


class Worker(GeventPyWSGIWorker):
    server_class = WSGIServer
    wsgi_handler = WSGIHandler


def create_app(global_config, **settings):
    settings = get_settings(global_config, **settings)

    config = Configurator(settings=settings)

    config.add_request_method(features.flag_enabled, name='feature')

    config.include('h.auth')
    config.include('h.sentry')

    # We have to include models and db to set up sqlalchemy metadata.
    config.include('h.models')
    config.include('h.db')
    config.include('h.api.db')

    # We have to include search to set up the `request.es` property.
    config.include('h.api.search')

    config.include('h.streamer')

    return config.make_wsgi_app()
