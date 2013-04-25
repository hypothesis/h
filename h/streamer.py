import json
import logging
import threading
import traceback
import Queue

from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection
from annotator import authz

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
        req2 = urllib2.Request(self.iriToUri(domain), headers=headers)
        soup2 = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req2))
        domain_title = soup2.title.string if soup2.title else domain

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
            'domain': domain,
            'domain_title': domain_title,
            'domain_stripped': domain_stripped,
            'favicon_link': icon_link
        }

class StreamerConnection(SockJSConnection):
    connections = set()

    def on_open(self, info):
      self.filter = {}
      self.connections.add(self)

    def on_message(self, msg):
      try:
        payload = json.loads(msg)
        if 'users' in payload:
            payload['users'] = set([x.strip() for x in payload['users'] if len(x.strip()) > 0])
        if 'actions' in payload:
            payload['actions'] = {x: bool(y) for x, y in payload['actions'].items()}
        if 'keywords' in payload:
            payload['keywords'] = set([x.strip() for x in payload['keywords'] if len(x.strip()) > 0])
        if 'threads' in payload:
            payload['threads'] = set([x.strip() for x in payload['threads'] if len(x.strip()) > 0])
        
        #Add new filter
        self.filter = payload
      except:
        log.info(traceback.format_exc())
        log.info('Failed to parse filter:' + str(msg))  

    def on_close(self):
        log.info('close')
        self.connections.remove(self)

def _init_streamer(port):
    StreamerRouter = SockJSRouter(StreamerConnection, '/streamer')

    app = web.Application(StreamerRouter.urls)
    app.listen(port) 
    ioloop.IOLoop.instance().start()

q = Queue.Queue()

def init_streamer(port = 5001):
    global _port
    _port = int(port)
    t = threading.Thread(target=_init_streamer, args=(port,))
    t2 = threading.Thread(target=process_filters)
    t.daemon = True
    t2.daemon = True
    t.start()
    t2.start()

def add_port():
    return { 'port' : _port }


def process_filters():
    while True:
        (annotation, action) = q.get()
        after_action(annotation, action)
        q.task_done()

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
                threads_filter = False
                intersect = list(filter['threads'] & set(annotation['references']))
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
    q.put((annotation, 'create'))

def after_update(annotation):
    q.put((annotation, 'update'))

def after_delete(annotation):
    q.put((annotation, 'delete'))

