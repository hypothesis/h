# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
from zope.interface import implementer

from memex.interfaces import IGroupService


class DefaultGroupContext(object):
    def __init__(self, id_):
        self.id_ = id_

    def __acl__(self):
        if self.id_ == '__world__':
            return [(security.Allow, security.Authenticated, 'write'),
                    (security.Allow, security.Everyone, 'read'),
                    security.DENY_ALL]
        return [security.DENY_ALL]


@implementer(IGroupService)
class DefaultGroupService(object):
    def find(self, id_):
        return DefaultGroupContext(id_)


def default_group_service_factory(context, request):
    return DefaultGroupService()
