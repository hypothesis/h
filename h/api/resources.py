# -*- coding: utf-8 -*-

from pyramid.security import Allow, Deny, Authenticated, Everyone

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


class Annotations(object):
    """
    Annotations is a container resource that exposes annotations as its
    children in the tree.
    """
    def __getitem__(self, key):
        instance = Annotation.fetch(key)
        if instance is None:
            raise KeyError(key)
        instance.__name__ = key
        instance.__parent__ = self
        return instance


class Root(Resource):
    def __acl__(self):
        return [
            (Allow, Authenticated, 'create'),
            (Allow, Everyone, 'search'),
        ]


def create_root(request):
    """
    Returns a new traversal tree root.
    """
    r = Root()
    r.add('annotations', Annotations())
    return r
