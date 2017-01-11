# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security

from memex import groups


class TestDefaultGroupContext(object):
    def test_world_group_acl(self):
        ctx = groups.DefaultGroupContext('__world__')
        assert ctx.__acl__() == [
            (security.Allow, security.Authenticated, 'write'),
            (security.Allow, security.Everyone, 'read'),
            security.DENY_ALL
        ]

    def test_acl_fallback(self):
        ctx = groups.DefaultGroupContext('foobar')
        assert ctx.__acl__() == [security.DENY_ALL]
