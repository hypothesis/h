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
import weakref

import psycogreen.gevent
from gevent.pool import Pool
from gunicorn.workers.ggevent import GeventPyWSGIWorker, PyWSGIHandler, PyWSGIServer
from ws4py import format_addresses

log = logging.getLogger(__name__)


class WebSocketWSGIHandler(PyWSGIHandler):
    """
    A WSGI handler that will perform the :rfc:`6455` upgrade and handshake before calling the WSGI application.

    If the incoming request doesn't have a `'Upgrade'` header, the handler will
    simply fallback to the gevent builtin's handler and process it as per
    usual.
    """

    def finalize_headers(self):  # pragma: no cover
        if self.environ.get("HTTP_UPGRADE", "").lower() == "websocket":
            # Middleware may yield from the empty upgrade
            # response, confusing this method into sending "Transfer-Encoding:
            # chunked" and, in turn, this confuses some strict WebSocket
            # clients.
            if not hasattr(self.result, "__len__") and self.result is not None:
                self.result = list(self.result)

            # ws4py 0.3.4 will try to pop the websocket from the environ
            # even if it doesn't exist, causing a key error.
            self.environ.setdefault("ws4py.websocket", None)

        super().finalize_headers()

    def run_application(self):  # pragma: no cover
        upgrade_header = self.environ.get("HTTP_UPGRADE", "").lower()
        if upgrade_header:
            # Build and start the HTTP response
            self.environ["ws4py.socket"] = (
                self.socket
                or self.environ[  # pylint: disable=protected-access
                    "wsgi.input"
                ].rfile._sock
            )
            self.result = self.application(self.environ, self.start_response) or []
            self.process_result()
            del self.environ["ws4py.socket"]
            self.socket = None
            self.rfile.close()

            ws = self.environ.pop("ws4py.websocket", None)
            if ws:
                ws_greenlet = self.server.pool.track(ws)
                ws_greenlet.join()
        else:
            super().run_application()


class GEventWebSocketPool(Pool):
    """
    Simple pool of bound websockets.

    Internally it uses a gevent group to track the websockets. The server
    should call the ``clear`` method to initiate the closing handshake when the
    server is shutdown.
    """

    def track(self, websocket):  # pragma: no cover
        log.debug("managing websocket %s", format_addresses(websocket))
        return self.spawn(websocket.run)

    def clear(self):  # pragma: no cover
        log.info("terminating server and all connected websockets")
        for greenlet in list(self):
            try:
                websocket = greenlet._run.__self__  # pylint: disable=protected-access
                if websocket:
                    websocket.close(1001, "Server is shutting down")
            except:  # pylint: disable=bare-except
                pass
            finally:
                self.discard(greenlet)


class WSGIServer(PyWSGIServer):
    """
    WSGI server that handles websockets.

    It simply tracks websockets and send them a proper closing
    handshake when the server terminates.

    Other than that, the server is the same as its
    :class:`gunicorn.workers.ggevent.PyWSGIServer` base.
    """

    # All instances of the server, allowing us to peek inside and see how many
    # greenlets we have running. This should really only ever have one value in
    # it
    instances = weakref.WeakSet()

    def __init__(self, *args, **kwargs):  # pragma: no cover
        super().__init__(*args, **kwargs)
        self.pool = GEventWebSocketPool()

        # Add this so we can report on it
        self.connection_pool = kwargs.get("spawn")
        self.instances.add(self)

    def stop(self, *args, **kwargs):  # pragma: no cover
        self.pool.clear()
        super().stop(*args, **kwargs)
        self.instances.remove(self)


class Worker(GeventPyWSGIWorker):
    server_class = WSGIServer
    wsgi_handler = WebSocketWSGIHandler

    def patch(self):  # pragma: no cover
        psycogreen.gevent.patch_psycopg()
        self.log.info("Made psycopg green")

        super().patch()
