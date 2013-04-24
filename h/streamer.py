import json
import logging
import threading
import traceback

from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection
from annotator import authz

log = logging.getLogger(__name__)

class StreamerConnection(SockJSConnection):
    connections = set()

    def on_open(self, info):
      self.filter = {}
      self.connections.add(self)

    def on_message(self, msg):
      try:
        payload = json.loads(msg)
        if 'users' in payload:
            payload['users'] = [x.strip() for x in payload['users']]
        if 'actions' in payload:
            payload['actions'] = {x: bool(y) for x, y in payload['actions'].items()}
        if 'keywords' in payload:
            payload['keywords'] = [x.strip() for x in payload['keywords']]
        if 'threads' in payload:
            payload['threads'] = [x.strip() for x in payload['threads']]
        
        #Add new filter
        self.filter = payload
      except:
        log.info(traceback.format_exc())
        log.info('Failed to parse filter:' + str(msg))  

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
    for connection in StreamerConnection.connections:
        try:
          filter = connection.filter
          if len(filter) > 0:
            user_filter = True
            if 'users' in filter:
              user = annotation['user'].split(':')[1].split('@')[0]
              user_filter = user in filter['users']

            action_filter =  True
            if 'actions' in filter:
              action_filter =  filter['actions'][action]

            keyword_filter = True
            if 'keywords' in filter:
                keyword_filter = False
                for keyword in filter['keywords']:
                  if annotation['text'].find(keyword) >= 0:
                    keyword_filter = True
                    break
            
            thread_filter = True
            if 'threads' in filter:
                keyword_filter = False
                intersect = [filter(lambda x: x in filter['threads'], sublist) for sublist in annotation['references']]
                if annotation['id'] in filter['threads'] or len(intersect) > 0:
                  thread_filter = True
                                  
            if user_filter and action_filter and keyword_filter and thread_filter:
              connection.send([annotation, action])                 
          else:
            #No filter, just send everything
            connection.send([annotation, action])
        except:
           log.info(traceback.format_exc())
           log.info('Filter error!')  
               
def after_save(annotation):
    after_action(annotation, 'create')    

def after_update(annotation):
    after_action(annotation, 'update')    

def after_delete(annotation):
    after_action(annotation, 'delete')    

