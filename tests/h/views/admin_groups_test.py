# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import pytest
import mock

# from h.models.auth_client import AuthClient, GrantType, ResponseType
from h.views import admin_groups
from h.views.admin_groups import GroupCreateController


def test_index_lists_groups_sorted_by_created_desc(pyramid_request, routes, factories, authority):
    groups = [factories.Group(created=datetime.datetime(2017, 8, 2)),
              factories.Group(created=datetime.datetime(2015, 2, 1)),
              factories.Group(),
              factories.Group(created=datetime.datetime(2013, 2, 1))]

    ctx = admin_groups.groups_index(None, pyramid_request)

    # We can't avoid getting the Public group back, which is created outside of
    # these tests' sphere of influence. Remove it as it is not feasible to
    # assert where it will appear in creation order.
    filtered_groups = list(filter(lambda group: group.pubid != u'__world__',
                                  ctx['results']))

    expected_groups = [groups[2], groups[0], groups[1], groups[3]]
    assert filtered_groups == expected_groups


def test_index_paginates_results(pyramid_request, routes, paginate):
    admin_groups.groups_index(None, pyramid_request)

    paginate.assert_called_once_with(pyramid_request, mock.ANY, mock.ANY)


class TestGroupCreateController(object):

    def test_get_sets_foo(self, pyramid_request):
        ctrl = GroupCreateController(pyramid_request)

        ctx = ctrl.get()

        assert 'foo' in ctx


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.session = mock.Mock(spec_set=['flash', 'get_csrf_token'])
    return pyramid_request


@pytest.fixture
def authority():
    return 'foo.com'


@pytest.fixture
def paginate(patch):
    return patch('h.views.admin_groups.paginator.paginate')


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('admin_groups', '/admin/groups')
    pyramid_config.add_route('admin_groups_create', '/admin/groups/new')
