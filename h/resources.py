try:
    import simplejson as json
except ImportError:
    import json

import urllib2

from datetime import datetime
from math import floor
from urlparse import urlparse, urlunparse

from dateutil.parser import parse
from dateutil.tz import tzutc

from horus import resources

from pyramid.interfaces import ILocation

from zope.interface import implementer

import BeautifulSoup
import re

from h import interfaces


import logging
log = logging.getLogger(__name__)


@implementer(ILocation)
class BaseResource(resources.BaseFactory):
    """Base Resource class from which all resources are derived"""

    __name__ = None
    __parent__ = None


class InnerResource(BaseResource):
    """Helper Resource class for constructing traversal contexts

    Classes which inherit from this should contain attributes which are either
    class constructors for classes whose instances provide the
    :class:`pyramid.interfaces.ILocation` interface else attributes which are,
    themselves, instances of such a class. Such attributes are treated as
    valid traversal children of the Resource whose path component is the name
    of the attribute.
    """

    def __getitem__(self, name):
        """
        Any class attribute which is an instance providing
        :class:`pyramid.interfaces.ILocation` will be returned as is.

        Attributes which are constructors for implementing classes will
        be replaced with a constructed instance by reifying the newly
        constructed resource in place of the attribute.

        Assignment to the sub-resources `__name__` and `__parent__` properties
        is handled automatically.
        """

        factory_or_resource = getattr(self, name, None)

        if factory_or_resource:
            if ILocation.implementedBy(factory_or_resource):
                inst = factory_or_resource(self.request)
                inst.__name__ = name
                inst.__parent__ = self
                setattr(self, name, inst)
                return inst

            if ILocation.providedBy(factory_or_resource):
                return factory_or_resource

        raise KeyError(name)


class RootFactory(InnerResource, resources.RootFactory):
    pass


class AppFactory(BaseResource):
    def __init__(self, request):
        super(AppFactory, self).__init__(request)

    @property
    def embed(self):
        env = {
            pkg: json.dumps(self.request.webassets_env[pkg].urls())
            for pkg in ['inject', 'jquery', 'raf']
        }
        env['app'] = "'%s'" % self.request.resource_url(self)
        return env

    @property
    def persona(self):
        request = self.request

        # Transition code until multiple sign-in is implemented
        if request.user:
            return {
                'username': request.user.username,
                'provider': request.host,
            }

        return None

    @property
    def personas(self):
        request = self.request

        # Transition code until multiple sign-in is implemented
        if request.user:
            return [self.persona]

        return []

    def __json__(self, request=None):
        return {
            name: getattr(self, name)
            for name in ['persona', 'personas']
        }


class Annotation(BaseResource, dict):
    def urlEncodeNonAscii(self, b):
        return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

    def iriToUri(self, iri):
        parts= urlparse(iri)
        return urlunparse(
            part.encode('idna') if parti==1 else self.urlEncodeNonAscii(part.encode('utf-8'))
            for parti, part in enumerate(parts)
        )
    
    def _url_values(self):
        # Getting the title of the uri.
        # hdrs magic is needed because urllib2 is forbidden to use with default
        # settings.
        agent = \
            "Mozilla/5.0 (X11; U; Linux i686) " \
            "Gecko/20071127 Firefox/2.0.0.11"
        headers = {'User-Agent': agent}
        req = urllib2.Request(self.iriToUri(self['uri']), headers=headers)
        result = urllib2.urlopen(req)
        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req))
        title = soup.title.string if soup.title else self['uri']

        # Getting the domain from the uri, and the same url magic for the
        # domain title.
        parsed_uri = urlparse(self['uri'])
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

    def _fuzzyTime(self, date):
        if not date: return ''
        converted = parse(date)
        delta = datetime.utcnow().replace(tzinfo=tzutc()) - converted
        delta = round(delta.total_seconds())

        minute = 60
        hour = minute * 60
        day = hour * 24
        week = day * 7
        month = day * 30

        if (delta < 30):
            fuzzy = 'moments ago'
        elif (delta < minute):
            fuzzy = str(int(delta)) + ' seconds ago'
        elif (delta < 2 * minute):
            fuzzy = 'a minute ago'
        elif (delta < hour):
            fuzzy = str(int(floor(delta / minute))) + ' minutes ago'
        elif (floor(delta / hour) == 1):
            fuzzy = '1 hour ago'
        elif (delta < day):
            fuzzy = str(int(floor(delta / hour))) + ' hours ago'
        elif (delta < day * 2):
            fuzzy = 'yesterday'
        elif (delta < month):
            fuzzy = str(int(round(delta / day))) + ' days ago'
        else:
            fuzzy = str(converted)

        return fuzzy

    def _userName(self, user):
        if not user or user == '': return 'Annotation deleted.'
        else:
            return user.split(':')[1].split('@')[0]

    def _nestlist(self, part, childTable):
        outlist = []
        if part is None: return outlist
        part = sorted(part, key=lambda reply: reply['created'], reverse=True)
        for reply in part:
            children = self._nestlist(childTable.get(reply['id']), childTable)
            del reply['created']
            reply['number_of_replies'] = len(children)
            outlist.append(reply)
            if len(children) > 0: outlist.append(children)
        return outlist

    @property
    def quote(self):
        if not 'target' in self: return ''
        quote = ''
        for target in self['target']:
            for selector in target['selector']:
                if selector['type'] == 'TextQuoteSelector':
                    quote = quote + selector['exact'] + ' '

        return quote

    @property
    def references(self):
        thread = self.get('thread')
        return thread.split('/') if thread else []

    @property
    def replies(self):
        request = self.request
        registry = request.registry
        store = registry.queryUtility(interfaces.IStoreClass)()

        childTable = {}
        if 'thread' in self:
            thread = '/'.join([self['thread'], self['id']])
        else:
            thread = self['id']

        replies = store.search(thread=thread)
        replies = sorted(replies, key=lambda reply: reply['created'])

        for reply in replies:
            # Add this to its parent.
            parent = reply['thread'].split('/')[-1]
            pointer = childTable.setdefault(parent, [])
            pointer.append({
                'id': reply['id'],
                'created': reply['created'],
                'text': reply['text'],
                'fuzzy_date': self._fuzzyTime(reply['updated']),
                'readable_user': self._userName(reply['user']),
            })

        # Create nested list form
        repl = self._nestlist(childTable.get(self['id']), childTable)
        return repl


class AnnotationFactory(BaseResource):
    def __getitem__(self, key):
        request = self.request
        registry = request.registry
        store = registry.queryUtility(interfaces.IStoreClass)()

        annotation = Annotation(request)
        annotation.__parent__ = self
        try:
          annotation.update(store.read(key))
        except:
          pass

        return annotation


def includeme(config):
    config.set_root_factory(RootFactory)
    config.add_route('index', '/')
    RootFactory.app = AppFactory
    RootFactory.a = AnnotationFactory
    config.add_route('streamer', '/stream/')