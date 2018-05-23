# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.groups import search


@pytest.mark.usefixtures('group_service')
class TestGroupAuthFilter(object):
    def test_fetches_readable_groups(self, pyramid_request, group_service):
        pyramid_request.user = mock.sentinel.user

        filter_ = search.GroupAuthFilter(pyramid_request)
        filter_({})

        group_service.groupids_readable_by.assert_called_once_with(mock.sentinel.user)

    def test_returns_terms_filter(self, pyramid_request, group_service):
        group_service.groupids_readable_by.return_value = ['group-a', 'group-b']

        filter_ = search.GroupAuthFilter(pyramid_request)
        result = filter_({})

        assert result == {'terms': {'group': ['group-a', 'group-b']}}

    @pytest.fixture
    def group_service(self, patch, pyramid_config):
        svc = patch('h.services.group.GroupService')
        pyramid_config.register_service(svc, name='group')
        return svc

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        return pyramid_request
