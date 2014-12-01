from gunicorn.workers.ggevent import GeventPyWSGIWorker, PyWSGIHandler
from ws4py.server.geventserver import WSGIServer, WebSocketWSGIHandler


class WSGIHandler(PyWSGIHandler, WebSocketWSGIHandler):
    pass


class Worker(GeventPyWSGIWorker):
    server_class = WSGIServer
    wsgi_handler = WSGIHandler
