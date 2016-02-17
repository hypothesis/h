# -*- coding: utf-8 -*-
from pyramid.security import Allow


class Root(object):
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

    def __init__(self, request):
        self.request = request


class UserStreamFactory(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        return {'q': 'user:{}'.format(key)}


class TagStreamFactory(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        return {'q': 'tag:{}'.format(key)}
