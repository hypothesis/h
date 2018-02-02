# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPNoContent, HTTPBadRequest

from h.views import api_groups as views


@pytest.mark.usefixtures('profile_group_service')
class TestGroups(object):
    def test_groups_proxies_to_service(self, pyramid_request, profile_group_service):
        views.groups(pyramid_request)

        assert profile_group_service.called_once()

    def test_groups_passes_authority_parameter(self, pyramid_request, profile_group_service):
        pyramid_request.params = {'authority': 'foo.com'}

        views.groups(pyramid_request)

        assert profile_group_service.called_once_with(pyramid_request, 'foo.com')

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.user = user
        pyramid_request.json_body = {}
        return pyramid_request

    @pytest.fixture
    def user(self, factories):
        return factories.User.build()

    @pytest.fixture
    def profile_group_service(self, pyramid_config):
        svc = mock.Mock()
        pyramid_config.register_service(svc, name='profile_group')
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
        service = mock.Mock(spec_set=['member_leave'])
        service.member_leave.return_value = None
        pyramid_config.register_service(service, name='group')
        return service

    @pytest.fixture
    def authenticated_userid(self, pyramid_config):
        userid = 'acct:bob@example.org'
        pyramid_config.testing_securitypolicy(userid)
        return userid
