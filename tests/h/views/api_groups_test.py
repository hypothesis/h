# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPNoContent, HTTPBadRequest, HTTPMovedPermanently

from .groups_test import FakeGroupService

from h.views import api_groups as views
from h.models import (Group, User)

@pytest.mark.usefixtures('group_service')
class TestRead(object):

    def test_read_noslug(self, pyramid_request, group_service):
        group = group_service.create(u'test_read_noslug', 'localhost', 0)
        pyramid_request.matchdict[u'pubid'] = group.pubid
        # request.route_path is not defined on DummyRequest
        def _route_path(route_name, pubid, slug):
            return '/api/groups/{pubid}/{slug}'.format(pubid=pubid, slug=slug)
        pyramid_request.route_path = _route_path
        with pytest.raises(HTTPMovedPermanently) as redirect_exc:
            views.read_noslug(group, pyramid_request)

    def test_get_group(self, pyramid_request, group_service):
        group = group_service.create(u'test_read_noslug', 'localhost', 0)
        pyramid_request.matchdict[u'slug'] = group.slug
        pyramid_request.matchdict[u'pubid'] = group.pubid
        response = views.get_group(group, pyramid_request)
        assert response
        for k in ('id', 'name', 'description'):
            assert k in response

    @pytest.fixture
    def group_service(self, pyramid_config):
        service = FakeGroupService()
        pyramid_config.register_service(service, name='group')
        return service


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
