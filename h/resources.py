# -*- coding: utf-8 -*-

from pyramid.security import Allow

from h.auth import role


class Root(object):
    __acl__ = [
        (Allow, role.Admin, 'admin_index'),
        (Allow, role.Staff, 'admin_index'),
        (Allow, role.Admin, 'admin_features'),
        (Allow, role.Admin, 'admin_nipsa'),
        (Allow, role.Admin, 'admin_admins'),
        (Allow, role.Admin, 'admin_staff'),
        (Allow, role.Admin, 'admin_users'),
        (Allow, role.Staff, 'admin_users'),
        (Allow, role.Admin, 'admin_badge'),
        (Allow, role.Admin, 'admin_groups'),
        (Allow, role.Staff, 'admin_groups'),
    ]

    def __init__(self, request):
        self.request = request
