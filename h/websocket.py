# -*- coding: utf-8 -*-
"""
The websocket server for Hypothesis.

This file contains a worker class for Gunicorn (:py:class:`h.websocket.Worker`)
and a stripped-down Pyramid application which exposes a single endpoint for
serving the "streamer" over the websocket.

Most of the code in this file: specifically the WebSocketWSGIHandler,
GEventWebSocketPool, and WSGIServer classes, are essentially lifted straight
from the ws4py codebase. We've made a number of modifications to fix bugs in
the (apparently unmaintained) ws4py code, and these are documented below:

1. Override WebSocketWSGIHandler.run_application due to the websocket server
   crashing with EBADF. A change in gevent (1.1) causes all sockets to be
   closed when a WSGI handler returns. ws4py starts a new greenlet for each
   new websocket connection used to return from the WSGI handler. The fix is
   taken from [1] and waits for the greenlet to finish before returning from
   the WSGI handler.

   [1]: https://github.com/Lawouach/WebSocket-for-Python/pull/180

   More information at:

   - https://github.com/Lawouach/WebSocket-for-Python/issues/170
   - https://github.com/gevent/gevent/issues/633

2. Fix GEventWebSocketPool so that if the set of greenlets changes while it is
   being closed it doesn't throw a "Set changed size during iteration"
   RuntimeError. See:

   - https://github.com/Lawouach/WebSocket-for-Python/issues/132

N.B. Portions of the ws4py code are used here under the terms of the MIT
license distributed with the ws4py project. Such code remains copyright (c)
2011-2015, Sylvain Hellegouarch.
"""

import logging

from gevent.pool import Pool
from gunicorn.workers.ggevent import (GeventPyWSGIWorker, PyWSGIHandler,
                                      PyWSGIServer)
from ws4py import format_addresses

from h.config import configure

log = logging.getLogger(__name__)


class WebSocketWSGIHandler(PyWSGIHandler):

    """
    A WSGI handler that will perform the :rfc:`6455` upgrade and handshake
    before calling the WSGI application.

    If the incoming request doesn't have a `'Upgrade'` header, the handler will
    simply fallback to the gevent builtin's handler and process it as per
    usual.
    """

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

        super(WebSocketWSGIHandler, self).finalize_headers()

    def run_application(self):
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
            super(WebSocketWSGIHandler, self).run_application()


class GEventWebSocketPool(Pool):

    """
    Simple pool of bound websockets.

    Internally it uses a gevent group to track the websockets. The server
    should call the ``clear`` method to initiate the closing handshake when the
    server is shutdown.
    """

    def track(self, websocket):
        log.debug("managing websocket %s" % format_addresses(websocket))
        return self.spawn(websocket.run)

    def clear(self):
        log.info("terminating server and all connected websockets")
        for greenlet in list(self):
            try:
                websocket = greenlet._run.im_self
                if websocket:
                    websocket.close(1001, 'Server is shutting down')
            except:  # noqa: E722
                pass
            finally:
                self.discard(greenlet)


class WSGIServer(PyWSGIServer):
    """
    WSGI server that simply tracks websockets and send them a proper closing
    handshake when the server terminates.

    Other than that, the server is the same as its
    :class:`gunicorn.workers.ggevent.PyWSGIServer` base.
    """
    def __init__(self, *args, **kwargs):
        super(WSGIServer, self).__init__(*args, **kwargs)
        self.pool = GEventWebSocketPool()

    def stop(self, *args, **kwargs):
        self.pool.clear()
        super(WSGIServer, self).stop(*args, **kwargs)


class Worker(GeventPyWSGIWorker):
    server_class = WSGIServer
    wsgi_handler = WebSocketWSGIHandler

    # Used by our gunicorn config to selectively monkeypatch psycopg2
    use_psycogreen = True


def create_app(global_config, **settings):
    config = configure(settings=settings)
    config.include('pyramid_services')

    config.include('h.auth')
    # Override the default authentication policy.
    config.set_authentication_policy('h.auth.WEBSOCKET_POLICY')

    config.include('h.authz')
    config.include('h.db')
    config.include('h.session')
    config.include('h.search')
    config.include('h.sentry')
    config.include('h.services')
    config.include('h.stats')

    # We include links in order to set up the alternative link registrations
    # for annotations.
    config.include('h.links')

    # And finally we add routes. Static routes are not resolvable by HTTP
    # clients, but can be used for URL generation within the websocket server.
    config.add_route('ws', '/ws')
    config.add_route('annotation', '/a/{id}', static=True)
    config.add_route('api.annotation', '/api/annotations/{id}', static=True)

    config.include('h.streamer')

    return config.make_wsgi_app()
