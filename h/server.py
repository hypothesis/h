from gunicorn.workers.ggevent import GeventPyWSGIWorker, PyWSGIHandler
from ws4py.server.geventserver import WSGIServer, WebSocketWSGIHandler


class WSGIHandler(PyWSGIHandler, WebSocketWSGIHandler):
    def finalize_headers(self):
        if self.environ.get('HTTP_UPGRADE') == 'websocket':
            # Middleware, like Raven, may yield from the empty upgrade response,
            # confusing this method into sending "Transfer-Encoding: chunked"
            # and, in turn, this confuses some strict WebSocket clients.
            if not hasattr(self.result, '__len__'):
                self.result = list(self.result)

            # ws4py 0.3.4 will try to pop the websocket from the environ
            # even if it doesn't exist, causing a key error.
            self.environ.setdefault('ws4py.websocket', None)

        super(WSGIHandler, self).finalize_headers()


class Worker(GeventPyWSGIWorker):
    server_class = WSGIServer
    wsgi_handler = WSGIHandler
