# -*- coding: utf-8 -*-
from pyramid.security import Allow

from h.api import resources as api
from h.api.resources import Resource


class UserStreamFactory(Resource):
    def __getitem__(self, key):
        query = {'q': 'user:{}'.format(key)}
        return Search(query=query)



class TagStreamFactory(Resource):
    def __getitem__(self, key):
        query = {'q': 'tag:{}'.format(key)}
        return Search(query=query)


class Annotation(api.Annotation):
    pass


class Annotations(api.Annotations):
    def factory(self, key):
        return Annotation(id=key)


class Stream(Resource):
    pass


class Root(Resource):
    __acl__ = [(Allow, 'group:__admin__', 'admin')]


def create_root(request):
    """
    Returns a new traversal tree root.
    """
    r = Root()
    r.add('api', api.create_root(request))
    r.add('a', Annotations(request))
    r.add('t', TagStreamFactory())
    r.add('u', UserStreamFactory())
    return r
