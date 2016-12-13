# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security

GROUPFINDER_KEY = 'memex.groupfinder'


class DefaultGroupContext(object):
    def __init__(self, id_):
        self.id_ = id_

    def __acl__(self):
        if self.id_ == '__world__':
            return [(security.Allow, security.Authenticated, 'write'),
                    (security.Allow, security.Everyone, 'read'),
                    security.DENY_ALL]
        return [security.DENY_ALL]


def find(request, id_):
    groupfinder = request.registry.get(GROUPFINDER_KEY)
    return groupfinder(request, id_)


def default_groupfinder(request, id_):
    return DefaultGroupContext(id_)


def set_groupfinder(config, func):
    config.registry[GROUPFINDER_KEY] = config.maybe_dotted(func)


def includeme(config):
    config.add_directive('memex_set_groupfinder', set_groupfinder)
    config.memex_set_groupfinder(default_groupfinder)
