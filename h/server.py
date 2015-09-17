# -*- coding: utf-8 -*-
from datetime import datetime

from gunicorn.workers.ggevent import GeventPyWSGIWorker, PyWSGIHandler
from gunicorn.workers.ggevent import GeventResponse
from ws4py.server.geventserver import WSGIServer, WebSocketWSGIHandler


class WSGIHandler(PyWSGIHandler, WebSocketWSGIHandler):
    def finalize_headers(self):
        if self.environ.get('HTTP_UPGRADE', '').lower() == 'websocket':
            # Middleware, like Raven, may yield from the empty upgrade response,
            # confusing this method into sending "Transfer-Encoding: chunked"
            # and, in turn, this confuses some strict WebSocket clients.
            if not hasattr(self.result, '__len__'):
                self.result = list(self.result)

            # ws4py 0.3.4 will try to pop the websocket from the environ
            # even if it doesn't exist, causing a key error.
            self.environ.setdefault('ws4py.websocket', None)

        super(WSGIHandler, self).finalize_headers()

    # Gunicorn does not handle gevent 1.1's wrapper around the logger yet.
    def log_request(self):
        start = datetime.fromtimestamp(self.time_start)
        finish = datetime.fromtimestamp(self.time_finish)
        response_time = finish - start
        resp_headers = getattr(self, 'response_headers', {})
        resp = GeventResponse(self.status, resp_headers, self.response_length)
        if hasattr(self, 'headers'):
            req_headers = [h.split(":", 1) for h in self.headers.headers]
        else:
            req_headers = []
        self.server.log.logger.access(resp, req_headers, self.environ,
                                      response_time)


class Worker(GeventPyWSGIWorker):
    server_class = WSGIServer
    wsgi_handler = WSGIHandler
