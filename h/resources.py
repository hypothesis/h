# -*- coding: utf-8 -*-
from pyramid.security import Allow

from h.api import resources as api
from h.api.resources import Resource


class UserStreamFactory(Resource):
    def __getitem__(self, key):
        query = {'q': 'user:{}'.format(key)}
        return Stream(query=query)



class TagStreamFactory(Resource):
    def __getitem__(self, key):
        query = {'q': 'tag:{}'.format(key)}
        return Stream(query=query)


class Annotation(api.Annotation):
    pass


class Annotations(api.Annotations):
    def factory(self, id, model):
        return Annotation(id, model)


class Stream(Resource):
    pass


class Root(Resource):
    __acl__ = [
        (Allow, 'group:__admin__', 'admin_index'),
        (Allow, 'group:__staff__', 'admin_index'),
        (Allow, 'group:__admin__', 'admin_features'),
        (Allow, 'group:__admin__', 'admin_nipsa'),
        (Allow, 'group:__admin__', 'admin_admins'),
        (Allow, 'group:__admin__', 'admin_staff'),
        (Allow, 'group:__admin__', 'admin_users'),
        (Allow, 'group:__staff__', 'admin_users'),
        (Allow, 'group:__admin__', 'admin_badge'),
        (Allow, 'group:__admin__', 'admin_groups'),
        (Allow, 'group:__staff__', 'admin_groups'),
    ]


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
