# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPNoContent, HTTPBadRequest

from h.views import api_groups as views
from h.services.list_groups import ListGroupsService
from h.services.group import GroupService


@pytest.mark.usefixtures('GroupJSONPresenter')
class TestGroups(object):

    def test_all_groups_proxies_to_service(self, anonymous_request, list_groups_service):
        views.groups(anonymous_request)

        list_groups_service.all_groups.assert_called_once_with(
            user=None,
            authority=None,
            document_uri=None
        )

    def test_all_groups_proxies_authority_param(self, anonymous_request, list_groups_service):
        anonymous_request.params['authority'] = 'foo.com'
        views.groups(anonymous_request)

        list_groups_service.all_groups.assert_called_once_with(
            user=None,
            authority='foo.com',
            document_uri=None
        )

    def test_all_groups_proxies_document_uri_param(self, anonymous_request, list_groups_service):
        anonymous_request.params['document_uri'] = 'http://example.com/thisthing.html'
        views.groups(anonymous_request)

        list_groups_service.all_groups.assert_called_once_with(
            user=None,
            authority=None,
            document_uri='http://example.com/thisthing.html'
        )

    def test_uses_presenter_for_formatting(self, anonymous_request, open_groups, list_groups_service, GroupJSONPresenter):  # noqa: N803
        list_groups_service.all_groups.return_value = open_groups

        views.groups(anonymous_request)

        assert GroupJSONPresenter.call_count == 2

    def test_returns_formatted_groups(self, anonymous_request, open_groups, list_groups_service, GroupJSONPresenter):  # noqa: N803
        list_groups_service.all_groups.return_value = open_groups
        GroupJSONPresenter.asdict.return_value = {'foo': 'bar'}

        result = views.groups(anonymous_request)

        assert result == [GroupJSONPresenter(group, None).asdict() for group in open_groups]

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.route_url = mock.Mock(return_value='/groups/foo')
        return pyramid_request

    @pytest.fixture
    def open_groups(self, factories):
        return [factories.OpenGroup(), factories.OpenGroup()]

    @pytest.fixture
    def list_groups_service(self, pyramid_config):
        svc = mock.create_autospec(ListGroupsService, spec_set=True, instance=True)
        pyramid_config.register_service(svc, name='list_groups')
        return svc

    @pytest.fixture
    def anonymous_request(self, pyramid_request):
        pyramid_request.user = None
        return pyramid_request

    @pytest.fixture
    def user_with_private_groups(self, factories):
        user = factories.User()
        user.groups = [factories.Group(), factories.Group()]
        return user


@pytest.mark.usefixtures('authenticated_userid', 'group_service')
class TestRemoveMember(object):

    def test_it_removes_current_user(self, shorthand_request, authenticated_userid, group_service):
        group = mock.sentinel.group

        views.remove_member(group, shorthand_request)

        group_service.member_leave.assert_called_once_with(group, authenticated_userid)

    def test_it_returns_no_content(self, shorthand_request):
        group = mock.sentinel.group

        response = views.remove_member(group, shorthand_request)

        assert isinstance(response, HTTPNoContent)

    def test_it_fails_with_username(self, username_request):
        group = mock.sentinel.group

        with pytest.raises(HTTPBadRequest):
            views.remove_member(group, username_request)

    @pytest.fixture
    def shorthand_request(self, pyramid_request):
        pyramid_request.matchdict['user'] = 'me'
        return pyramid_request

    @pytest.fixture
    def username_request(self, pyramid_request):
        pyramid_request.matchdict['user'] = 'bob'
        return pyramid_request

    @pytest.fixture
    def group_service(self, pyramid_config):
        service = mock.create_autospec(GroupService, spec_set=True, instance=True)
        pyramid_config.register_service(service, name='group')
        return service

    @pytest.fixture
    def authenticated_userid(self, pyramid_config):
        userid = 'acct:bob@example.org'
        pyramid_config.testing_securitypolicy(userid)
        return userid


@pytest.fixture
def GroupJSONPresenter(patch):  # noqa: N802
    return patch('h.views.api_groups.GroupJSONPresenter')


@pytest.fixture
def GroupsJSONPresenter(patch):  # noqa: N802
    return patch('h.views.api_groups.GroupsJSONPresenter')
