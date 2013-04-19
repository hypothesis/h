import json
import logging
import threading

from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection
from annotator import authz

log = logging.getLogger(__name__)

class StreamerConnection(SockJSConnection):
    connections = set()

    def on_open(self, info):
	self.connections.add(self)

    def on_message(self, msg):
	pass
        #Json configuration will come here later

    def on_close(self):
	self.connections.remove(self)

def _init_streamer(port):
    StreamerRouter = SockJSRouter(StreamerConnection, '/streamer')

    app = web.Application(StreamerRouter.urls)
    app.listen(port) 
    ioloop.IOLoop.instance().start()

def init_streamer(port = 5001):
    global _port
    _port = int(port)
    t = threading.Thread(target=_init_streamer, args=(port,))
    t.daemon = True
    t.start()

def add_port():
    return { 'port' : _port }

def after_action(annotation, action):
    if not authz.authorize(annotation, 'read'): return
    for connection in StreamerConnection.connections :
    	connection.send([annotation, action])

def after_save(annotation):
    after_action(annotation, 'save')    

def after_update(annotation):
    after_action(annotation, 'update')    

def after_delete(annotation):
    after_action(annotation, 'delete')    

