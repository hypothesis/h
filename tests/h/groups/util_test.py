# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security

from h.groups import util


def test_world_group_acl():
    group = util.WorldGroup('example.com')

    assert group.__acl__() == [
        (security.Allow, security.Everyone, 'read'),
        (security.Allow, 'authority:example.com', 'write'),
        security.DENY_ALL,
    ]


def test_world_group_name():
    group = util.WorldGroup('example.com')

    assert group.name == 'Public'


def test_world_group_pubid():
    group = util.WorldGroup('example.com')

    assert group.pubid == '__world__'


def test_world_group_is_public():
    group = util.WorldGroup('example.com')

    assert group.is_public
