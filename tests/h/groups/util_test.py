# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from pyramid import security

from h.groups import util


class TestWorldGroup(object):
    def test_acl(self, group):
        assert group.__acl__() == [
            (security.Allow, security.Everyone, 'read'),
            (security.Allow, 'authority:example.com', 'write'),
            security.DENY_ALL,
        ]

    def test_name(self, group):
        assert group.name == 'Public'

    def test_pubid(self, group):
        assert group.pubid == '__world__'

    def test_is_public(self, group):
        assert group.is_public

    def test_creator(self, group):
        assert group.creator is None

    @pytest.fixture
    def group(self):
        return util.WorldGroup('example.com')
