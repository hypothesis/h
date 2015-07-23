# -*- coding: utf-8 -*-
from pyramid import security

from .api import create_root as create_api
from .models import Annotation


class Resource(dict):
    """
    Resource is an entry in the traversal tree.
    """
    __name__ = None
    __parent__ = None

    def add(self, name, obj):
        """
        Adds obj as a child resource with the given name. Automatically sets
        the __name__ and __parent__ properties of the child resource object.
        """
        obj.__name__ = name
        obj.__parent__ = self
        self[name] = obj


class UserStreamFactory(Resource):
    def __getitem__(self, key):
        return Stream(stream_type='user', stream_key=key)


class TagStreamFactory(Resource):
    def __getitem__(self, key):
        return Stream(stream_type='tag', stream_key=key)


class AnnotationFactory(Resource):
    def __getitem__(self, key):
        annotation = Annotation.fetch(key)
        if annotation is None:
            raise KeyError(key)
        annotation.__name__ = key
        annotation.__parent__ = self

        return annotation


class Application(Resource):
    pass


class Stream(Resource):
    pass


class Root(Resource):
    __acl__ = [
        (security.Allow, 'group:admin', security.ALL_PERMISSIONS),
        (security.Allow, security.Authenticated, 'authenticated'),
    ]


def create_root(request):
    """
    Returns a new traversal tree root.
    """
    r = Root()
    r.add('api', create_api(request))
    r.add('app', Application())
    r.add('stream', Stream())
    r.add('a', AnnotationFactory())
    r.add('t', TagStreamFactory())
    r.add('u', UserStreamFactory())
    return r
