# -*- coding: utf-8 -*-

from pyramid.security import Allow, Authenticated

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
    __acl__ = [
        (Allow, Authenticated, 'create'),
        (Allow, 'group:admin', 'admin'),
    ]


def create_root(_):
    """
    Returns a new traversal tree root.
    """
    r = Root()
    r.add('annotations', Annotations())
    return r
