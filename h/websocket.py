# -*- coding: utf-8 -*-
"""
The websocket server for Hypothesis.

This file contains a worker class for Gunicorn (:py:class:`h.websocket.Worker`)
and a stripped-down Pyramid application which exposes a single endpoint for
serving the "streamer" over the websocket.
"""

import gevent
from gunicorn.workers.ggevent import GeventPyWSGIWorker
from gunicorn.workers.ggevent import PyWSGIHandler
from ws4py.server.geventserver import WSGIServer
from ws4py.server.geventserver import WebSocketWSGIHandler

from h import features
from h.config import configure


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

    def run_application(self):
        # Override run_application from ws4py due to the websocket server
        # crashing with EBADF. A change in gevent (1.1) causes all sockets to be
        # closed when a WSGI handler returns. ws4py starts a new greenlet for
        # each new websocket connection used to return from the WSGI handler.
        # The fix is taken from [1] and waits for the greenlet to finish before
        # returning from the WSGI handler.
        #
        # [1]: https://github.com/Lawouach/WebSocket-for-Python/pull/180
        #
        # More information at:
        # - https://github.com/Lawouach/WebSocket-for-Python/issues/170
        # - https://github.com/gevent/gevent/issues/633

        upgrade_header = self.environ.get('HTTP_UPGRADE', '').lower()
        if upgrade_header:
            # Build and start the HTTP response
            self.environ['ws4py.socket'] = self.socket or self.environ['wsgi.input'].rfile._sock
            self.result = self.application(self.environ, self.start_response) or []
            self.process_result()
            del self.environ['ws4py.socket']
            self.socket = None
            self.rfile.close()

            ws = self.environ.pop('ws4py.websocket', None)
            if ws:
                ws_greenlet = self.server.pool.track(ws)
                ws_greenlet.join()
        else:
            gevent.pywsgi.WSGIHandler.run_application(self)


class Worker(GeventPyWSGIWorker):
    server_class = WSGIServer
    wsgi_handler = WSGIHandler

    # Used by our gunicorn config to selectively monkeypatch psycopg2
    use_psycogreen = True


def create_app(global_config, **settings):
    config = configure(settings=settings)

    config.add_request_method(features.Client, name='feature', reify=True)

    config.include('h.auth')
    config.include('h.sentry')
    config.include('h.stats')

    # We have to include models and db to set up sqlalchemy metadata.
    config.include('h.models')
    config.include('h.db')
    config.include('h.api.db')

    # We have to include search to set up the `request.es` property.
    config.include('h.api.search')

    config.include('h.streamer')

    return config.make_wsgi_app()
