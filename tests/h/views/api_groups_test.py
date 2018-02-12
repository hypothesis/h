# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPNoContent, HTTPBadRequest

from h.views import api_groups as views
from h.services.list_groups import ListGroupsService
from h.services.group import GroupService


class TestGroups(object):
    def test_groups_proxies_to_service(self, pyramid_request, list_groups_service):
        views.groups(pyramid_request)

        list_groups_service.all_groups.assert_called_once()

    def test_groups_passes_authority_parameter(self, pyramid_request, list_groups_service):
        pyramid_request.params = {'authority': 'foo.com'}

        views.groups(pyramid_request)

        c_args, c_kwargs = list_groups_service.all_groups.call_args
        assert c_kwargs['authority'] == 'foo.com'

    def test_groups_passes_document_uri_parameter(self, pyramid_request, list_groups_service):
        pyramid_request.params = {'document_uri': 'foo.example.com'}

        views.groups(pyramid_request)

        c_args, c_kwargs = list_groups_service.all_groups.call_args
        assert c_kwargs['document_uri'] == 'foo.example.com'

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.user = user
        pyramid_request.json_body = {}
        return pyramid_request

    @pytest.fixture
    def user(self, factories):
        return factories.User.build()

    @pytest.fixture
    def list_groups_service(self, pyramid_config):
        svc = mock.create_autospec(ListGroupsService, spec_set=True, instance=True)
        pyramid_config.register_service(svc, name='list_groups')
        return svc


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
