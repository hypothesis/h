# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPNoContent

from h.views import api_groups as views


@pytest.mark.usefixtures('authenticated_userid', 'group_service')
class TestRemoveMember(object):

    def test_it_removes_current_user(self, pyramid_request, authenticated_userid, group_service):
        group = mock.sentinel.group

        views.remove_member(group, pyramid_request)

        group_service.member_leave.assert_called_once_with(group, authenticated_userid)

    def test_it_returns_no_content(self, pyramid_request):
        group = mock.sentinel.group

        response = views.remove_member(group, pyramid_request)

        assert isinstance(response, HTTPNoContent)

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
