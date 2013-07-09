try:
    import simplejson as json
except ImportError:
    import json

from horus import resources

from pyramid.decorator import reify
from pyramid.interfaces import ILocation

from zope.interface import implementer

from h import interfaces
from h.models import get_session

import logging
log = logging.getLogger(__name__)

from models import AnnotationModerated


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
            # Add this to its parent.
            parent = reply.get('references', [])[-1]
            pointer = childTable.setdefault(parent, [])
            pointer.append(reply)

        # Create nested list form
        return self._nestlist(childTable.get(self['id']), childTable)


class Streamer(BaseResource, dict):
    pass


class AnnotationFactory(BaseResource):
    def __getitem__(self, key):
        request = self.request
        registry = request.registry
        store = registry.queryUtility(interfaces.IStoreClass)(request)

        annotation = Annotation(request)
        annotation.__name__ = key
        annotation.__parent__ = self
        try:
            annotation.update(store.read(key))
        except:
            pass

        return annotation


class UserStream(BaseResource, dict):
    pass


class UserStreamFactory(BaseResource):
    def __getitem__(self, key):
        #Check if user exists
        request = self.request
        registry = request.registry
        User = registry.getUtility(interfaces.IUserClass)
        user = User.get_by_username(request, key)
        if user is not None:
            return UserStream(request)


class AnnotationModeratedResource(Annotation):
    pass


class ModerationActionResource(BaseResource, dict):
    def __getitem__(self, key):
        # key is annotation id.
        # Creating AnnotationModeratedResource
        request = self.request
        registry = request.registry
        store = registry.queryUtility(interfaces.IStoreClass)(request)
        annot_moder_res = AnnotationModeratedResource(request)
        annot_moder_res.__parent__ = self
        try:
            annot_moder_res.update(store.read(key))
            # Adding AnnotationModerated object
            annot_moder = AnnotationModerated.get_add_item(key, user_email,
                                                           session)
            annot_moder_res.annot_moder = annot_moder
        except:
            pass
        return  annot_moder_res


class ModerationActionFactory(BaseResource):
    def __getitem__(self, key):
        # key is moderation action type.
        request = self.request
        moder_act_res = ModerationActionResource(request)
        moder_act_res.update({'action_type' : key})
        return moder_act_res


def includeme(config):
    config.set_root_factory(RootFactory)
    config.add_route('index', '/')
    RootFactory.app = AppFactory
    RootFactory.a = AnnotationFactory
    RootFactory.stream = Streamer
    RootFactory.u = UserStreamFactory
    RootFactory.act = ModerationActionFactory
