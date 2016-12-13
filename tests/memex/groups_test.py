# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
from pyramid import security
import pytest

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


class TestFind(object):
    def test_calls_groupfinder(self, pyramid_config, pyramid_request):
        groupfinder = mock.Mock()
        pyramid_config.registry[groups.GROUPFINDER_KEY] = groupfinder

        groups.find(pyramid_request, mock.sentinel.groupid)

        groupfinder.assert_called_once_with(pyramid_request, mock.sentinel.groupid)

    def test_returns_groupfinder_result(self, pyramid_config, pyramid_request):
        groupfinder = mock.Mock(return_value=mock.sentinel.groupcontext)
        pyramid_config.registry[groups.GROUPFINDER_KEY] = groupfinder

        result = groups.find(pyramid_request, mock.sentinel.groupid)

        assert result == mock.sentinel.groupcontext


class TestDefaultGroupfinder(object):
    def test_returns_default_context(self):
        result = groups.default_groupfinder(mock.sentinel.request, mock.sentinel.groupid)
        assert isinstance(result, groups.DefaultGroupContext)

    def test_sets_given_groupid(self):
        result = groups.default_groupfinder(mock.sentinel.request, mock.sentinel.groupid)
        assert result.id_ == mock.sentinel.groupid


class TestSetGroupfinder(object):
    def test_stores_given_groupfinder_in_registry(self, pyramid_config):
        groups.set_groupfinder(pyramid_config, mock.sentinel.groupfinder)

        assert pyramid_config.registry[groups.GROUPFINDER_KEY] == mock.sentinel.groupfinder

    def test_resolves_dotted_path(self, pyramid_config):
        pyramid_config.maybe_dotted = mock.Mock()

        groups.set_groupfinder(pyramid_config, mock.sentinel.groupfinder)

        pyramid_config.maybe_dotted.assert_called_once_with(mock.sentinel.groupfinder)

    def test_sets_dotted_path_resolved_object(self, pyramid_config):
        pyramid_config.maybe_dotted = mock.Mock()

        groups.set_groupfinder(pyramid_config, mock.sentinel.groupfinder)

        assert pyramid_config.registry[groups.GROUPFINDER_KEY] == pyramid_config.maybe_dotted.return_value


class TestIncludeme(object):
    def test_sets_default_groupfinder(self, testconfig):
        groups.includeme(testconfig)
        testconfig.memex_set_groupfinder.assert_called_once_with(groups.default_groupfinder)

    @pytest.fixture
    def testconfig(self):
        return mock.Mock(spec_set=[
            'add_directive',
            'memex_set_groupfinder',
        ])
