# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.groups import util


class TestFetchGroup(object):
    def test_it_returns_the_correct_group(self, pyramid_request, factories):
        groups = [factories.Group() for _ in xrange(3)]
        assert util.fetch_group(pyramid_request, groups[1].pubid) == groups[1]

    def test_it_returns_none_when_group_missing(self, pyramid_request, factories):
        # create a group
        factories.Group()

        assert util.fetch_group(pyramid_request, 'bogus') is None

    def test_it_returns_an_object_implementing_acl(self, pyramid_request, factories):
        group = factories.Group()

        result = util.fetch_group(pyramid_request, group.pubid)
        # make sure this call doesn't raise
        result.__acl__()
