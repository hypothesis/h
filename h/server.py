from gunicorn.workers.ggevent import GeventPyWSGIWorker, PyWSGIHandler
from ws4py.server.geventserver import WSGIServer, WebSocketWSGIHandler


class WSGIHandler(PyWSGIHandler, WebSocketWSGIHandler):
    def finalize_headers(self):
        # Middleware may yield from the empty upgrade response, confusing this
        # method into sending "Transfer-Encoding: chunked" and, in turn, this
        # confuses some strict WebSocket clients.
        for name, value in self.response_headers:
            if name == 'Upgrade' and value == 'websocket':
               return
        super(WSGIHandler, self).finalize_headers()


class Worker(GeventPyWSGIWorker):
    server_class = WSGIServer
    wsgi_handler = WSGIHandler
