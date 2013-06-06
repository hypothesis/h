try:
    import simplejson as json
except ImportError:
    import json

from urlparse import urlparse, urlunparse
from datetime import datetime
from math import floor
import traceback
import requests
import re

from dateutil.parser import parse
from dateutil.tz import tzutc

from horus import resources

from pyramid.decorator import reify
from pyramid.interfaces import ILocation

from zope.interface import implementer

import BeautifulSoup

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

    def _url_values(self, uri = None):
        if not uri: uri = self['uri']
        # Getting the title of the uri.
        try:
            r = requests.get(self.iriToUri(uri), verify=False)
            soup = BeautifulSoup.BeautifulSoup(r.content)
            title = soup.title.string if soup.title else uri

            # Favicon
            favlink = soup.find("link", rel="shortcut icon")
        except:
            log.info('Error opening url')
            log.info(traceback.format_exc())
            title = uri
            favlink = None

        # Getting the domain from the uri, and the same url magic for the
        # domain title.
        parsed_uri = urlparse(uri)
        domain = '{}://{}/'.format(parsed_uri[0], parsed_uri[1])
        domain_stripped = parsed_uri[1]
        if parsed_uri[1].lower().startswith('www.'):
            domain_stripped = domain_stripped[4:]

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

    def _fuzzyTime(self, date):
        if not date: return ''
        converted = parse(date)
        time_delta = datetime.utcnow().replace(tzinfo=tzutc()) - converted
        delta = round(time_delta.total_seconds())

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
            when = datetime.now() - time_delta
            time = when.strftime('%X')
            fuzzy = when.strftime('%c').replace(time, '').strip()

        return fuzzy

    def _userName(self, user):
        if not user or user == '': return 'Annotation deleted.'
        else:
            return user.split(':')[1].split('@')[0]

    def _nestlist(self, annotations, childTable):
        outlist = []
        if annotations is None: return outlist

        annotations = sorted(
            annotations,
            key=lambda reply: reply['created'],
            reverse=True
        )

        for a in annotations:
            children = self._nestlist(childTable.get(a['id']), childTable)
            a['reply_count'] = \
                sum(c['reply_count'] for c in children) + len(children)
            a['replies'] = children
            outlist.append(a)
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

    @reify
    def referrers(self):
        request = self.request
        registry = request.registry
        store = registry.queryUtility(interfaces.IStoreClass)(request)
        return store.search(references=self['id'])

    @reify
    def replies(self):
        childTable = {}

        for reply in self.referrers:
            reply.update({
                'date': self._fuzzyTime(reply['created']),
                'user': self._userName(reply['user']),
            })

            # Add this to its parent.
            parent = reply.get('references', [])[-1]
            pointer = childTable.setdefault(parent, [])
            pointer.append(reply)

        # Create nested list form
        return self._nestlist(childTable.get(self['id']), childTable)


class AnnotationFactory(BaseResource):
    def __getitem__(self, key):
        request = self.request
        registry = request.registry
        store = registry.queryUtility(interfaces.IStoreClass)(request)

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
