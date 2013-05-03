import json
import threading
import traceback

import urllib2
from urlparse import urlparse, urlunparse
import BeautifulSoup
import re
import Queue

from tornado import web, ioloop, httpserver
import ssl
from sockjs.tornado import SockJSRouter, SockJSConnection
from jsonschema import validate
import jsonpointer

from annotator import authz

import logging
log = logging.getLogger(__name__)

class UrlAnalyzer(dict):
    def urlEncodeNonAscii(self, b):
        return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

    def iriToUri(self, iri):
        parts= urlparse(iri)
        return urlunparse(
            part.encode('idna') if parti==1 else self.urlEncodeNonAscii(part.encode('utf-8'))
            for parti, part in enumerate(parts)
        )

    def _url_values(self, uri = None):
        if not uri: uri = self['uri']
        # Getting the title of the uri.
        # hdrs magic is needed because urllib2 is forbidden to use with default
        # settings.
        agent = \
            "Mozilla/5.0 (X11; U; Linux i686) " \
            "Gecko/20071127 Firefox/2.0.0.11"
        headers = {'User-Agent': agent}
        req = urllib2.Request(self.iriToUri(uri), headers=headers)
        result = urllib2.urlopen(req)
        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req))
        title = soup.title.string if soup.title else uri

        # Getting the domain from the uri, and the same url magic for the
        # domain title.
        parsed_uri = urlparse(uri)
        domain = '{}://{}/'.format(parsed_uri[0], parsed_uri[1])
        domain_stripped = parsed_uri[1]
        if parsed_uri[1].lower().startswith('www.'):
            domain_stripped = domain_stripped[4:]

        # Favicon
        favlink = soup.find("link", rel="shortcut icon")
        # Check for local/global link.
        if favlink:
            href = favlink['href']
            if href.startswith('//') or href.startswith('http'):
                icon_link = href
            else:
                icon_link = domain + href
        else:
            icon_link = ''

        return {
            'title': title,
            'source': domain,
            'source_stripped': domain_stripped,
            'favicon_link': icon_link
        }

filter_schema = {
    "type" : "object",
    "properties" : {
        "name" : {"type" : "string", "optional" : True},
        "match_policy" : {
            "type" : "string", 
            "enum" : ["include_any","include_all","exclude_any","exclude_all"]
        },
        "actions" : {
            "create" : { "type" : "boolean", "default" :  True},
            "edit" : { "type" : "boolean", "default" :  True},
            "delete" : { "type" : "boolean", "default" :  True},
        },
        "clauses" : {
            "type" : "array",
            "items": {
                "field" : { "type" : "string", "format": "json-pointer"},
                "operator" : {
                    "type" : "string",
                    "enum" : ["equals","matches","lt","le","gt","ge","one_of"]
                },
                "value" : "object"
            }
        }
    },
    "required" : ["match_policy","clauses","actions"]
}

class FilterHandler(object):
    def __init__(self, filter_json):
        self.filter = filter_json

    def _userName(self, user):
        if not user or user == '': return 'Annotation deleted.'
        else: return user.split(':')[1].split('@')[0]

    #operators
    def equals(self, a, b): return a == b
    def matches(self, a, b): return a in b
    def lt(self, a, b): return a < b
    def le(self, a, b): return a <= b
    def gt(self, a, b): return a > b
    def ge(self, a, b): return a >= b
    def one_of(self, a, b): return a in b
        
    def evaluate_clause(self, clause, target):
        field_value = resolve_pointer(target, clause['field'], None)
        if clause['field'] == 'user':
            field_value = self._userName(field_value)
        if field_value is None:
            return False
        else: return getattr(self, clause['operator'])(field_value, clause['value'])
    
    #match_policies
    def include_any(self, target):
        for clause in self.filter['clauses']:
            if self.evaluate_clause(clause, target): return True
        return False

    def include_all(self, target):
        for clause in self.filter['clauses']:
            if not self.evaluate_clause(clause, target): return False
        return True

    def exclude_all(self, target):
        for clause in self.filter['clauses']:
            if not self.evaluate_clause(clause, target): return True
        return False

    def exclude_any(self, target):
        for clause in self.filter['clauses']:
            if self.evaluate_clause(clause, target): return False
        return True

    def match(self, target):
        return getattr(self, self.filter['match_policy'])(target)

class StreamerConnection(SockJSConnection):
    connections = set()

    def on_open(self, info):
      self.filter = {}
      self.connections.add(self)

    def on_message(self, msg):
      try:          
        payload = json.loads(msg)
        #Let's try to validate the schema
        validate(payload, filter_schema)                
        self.filter = FilterHandler(payload)
      except:
        log.info(traceback.format_exc())
        log.info('Failed to parse filter:' + str(msg))
        self.close()

    def on_close(self):
        log.info('closing ' + str(self))
        self.connections.remove(self)

def _init_streamer(port, ssl_pem = None):
    StreamerRouter = SockJSRouter(StreamerConnection, '/streamer')
    app = web.Application(StreamerRouter.urls)
    if not ssl_pem:
        app.listen(port)
    else:  
        http_server = httpserver.HTTPServer(app,     
            ssl_options=dict(
                certfile=ssl_pem,
                keyfile=ssl_pem))
        http_server.listen(port)
    
    ioloop.IOLoop.instance().start()

q = Queue.Queue()

def init_streamer(port = 5001, ssl_pem = None):
    global _port
    _port = int(port)
    t = threading.Thread(target=_init_streamer, args=(port, ssl_pem))
    t2 = threading.Thread(target=process_filters)
    t.daemon = True
    t2.daemon = True
    t.start()
    t2.start()

def add_port():
    return { 'port' : _port }


def process_filters():
    url_analyzer = UrlAnalyzer()
    while True:
        (annotation, action) = q.get(True)
        annotation.update(url_analyzer._url_values(annotation['uri']))
        annotation.update({'action' : action})
        after_action(annotation, action)
        q.task_done()

def after_action(annotation, action):
    if not authz.authorize(annotation, 'read'): return
    
    for connection in StreamerConnection.connections:
        try:
          if connection.filter.match(annotation) : 
            connection.send([annotation, action])                 
        except:
           log.info(traceback.format_exc())
           log.info('Filter error!')  
               
def after_save(annotation):
    q.put((annotation, 'create'))

def after_update(annotation):
    q.put((annotation, 'update'))

def after_delete(annotation):
    q.put((annotation, 'delete'))

