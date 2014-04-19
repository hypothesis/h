# -*- coding: utf-8 -*-
import logging
import json

from pyramid.decorator import reify
from pyramid.interfaces import ILocation
from pyramid.security import Allow, Authenticated, Everyone, ALL_PERMISSIONS
from pyramid import httpexceptions
from zope.interface import implementer

from h import interfaces, security

log = logging.getLogger(__name__)  # pylint: disable=C0103


@implementer(ILocation)
class BaseResource(dict):
    """Base Resource class from which all resources are derived"""

    __name__ = None
    __parent__ = None

    def __init__(self, request, **kwargs):
        self.request = request
        super(BaseResource, self).__init__(kwargs)


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
            try:
                if ILocation.implementedBy(factory_or_resource):
                    inst = factory_or_resource(self.request)
                    inst.__name__ = name
                    inst.__parent__ = self
                    return inst
            except TypeError:
                pass

            try:
                if ILocation.providedBy(factory_or_resource):
                    return factory_or_resource
            except TypeError:
                pass

        raise KeyError(name)


@implementer(interfaces.IStreamResource)
class Stream(BaseResource):
    pass


class UserStreamFactory(BaseResource):
    def __getitem__(self, key):
        return Stream(self.request, stream_type='user', stream_key=key)


class TagStreamFactory(BaseResource):
    def __getitem__(self, key):
        return Stream(self.request, stream_type='tag', stream_key=key)


class RootFactory(Stream, InnerResource):
    @property
    def __acl__(self):
        defaultlist = [
            (Allow, 'group:admin', ALL_PERMISSIONS),
            (Allow, Authenticated, 'view'),
            (Allow, security.Authorizations, 'account'),
        ]
        return defaultlist


    @property
    def embed(self):
        env = {
            pkg: json.dumps(self.request.webassets_env[pkg].urls())
            for pkg in ['inject', 'jquery', 'raf']
        }
        options = {}
        if not self.request.GET.get('light', False):
            options.update({
                'Heatmap': {
                    'container': '.annotator-frame',
                },
                'Toolbar': {
                    'container': '.annotator-frame',
                },
            })
        env['app'] = json.dumps(self.request.resource_url(self, 'app'))
        env['options'] = json.dumps(options)
        env['role'] = json.dumps(self.request.GET.get('role', 'host'))
        return env

    @property
    def persona(self):
        request = self.request

        # Transition code until multiple sign-in is implemented
        if request.user:
            return {
                'username': request.user.username,
                'provider': request.server_name,
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
    @property
    def __acl__(self):
        acl = []
        # Convert annotator-store roles to pyramid principals
        for action, roles in self.get('permissions', {}).items():
            for role in roles:
                if role.startswith('group:'):
                    if role == 'group:__world__':
                        principal = Everyone
                    elif role == 'group:__authenticated__':
                        principal = Authenticated
                    elif role == 'group:__consumer__':
                        raise NotImplementedError("API consumer groups")
                    else:
                        principal = role
                elif role.startswith('acct:'):
                    principal = role
                else:
                    raise ValueError(
                        "Unrecognized role '%s' in annotation '%s'" %
                        (role, self.get('id'))
                    )

                # Append the converted rule tuple to the ACL
                rule = (Allow, principal, action)
                acl.append(rule)

        if acl:
            return acl
        else:
            # If there is no acl, it's an admin party!
            return [(Allow, Everyone, ALL_PERMISSIONS)]

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


class AnnotationFactory(BaseResource):
    def __getitem__(self, key):
        request = self.request
        registry = request.registry
        store = registry.queryUtility(interfaces.IStoreClass)(request)
        data = ''

        try:
            data = store.read(key)
        except httpexceptions.HTTPException as e:
            # We want to add our custom error message for unauthorized errors
            if e.status_code != 401:
                raise e

        annotation = Annotation(request)
        annotation.__name__ = key
        annotation.__parent__ = self

        annotation.update(data)

        return annotation


def includeme(config):
    config.set_root_factory(RootFactory)
    config.add_route('index', '/')
    RootFactory.a = AnnotationFactory
    RootFactory.stream = Stream
    RootFactory.u = UserStreamFactory
    RootFactory.t = TagStreamFactory

    if not config.registry.queryUtility(interfaces.IAnnotationClass):
        config.registry.registerUtility(Annotation, interfaces.IAnnotationClass)
