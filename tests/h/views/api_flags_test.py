# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPNoContent

from h.views import api_flags as views


@pytest.mark.usefixtures('flag_service')
class TestCreate(object):
    def test_it_flags_annotation(self, pyramid_request, flag_service):
        context = mock.Mock()

        views.create(context, pyramid_request)

        flag_service.create.assert_called_once_with(pyramid_request.authenticated_user,
                                                    context.annotation)

    def test_it_returns_no_content(self, pyramid_request):
        context = mock.Mock()

        response = views.create(context, pyramid_request)
        assert isinstance(response, HTTPNoContent)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.authenticated_user = mock.Mock()
        pyramid_request.json_body = {}
        return pyramid_request

    @pytest.fixture
    def flag_service(self, pyramid_config):
        flag_service = mock.Mock(spec_set=['create'])
        pyramid_config.register_service(flag_service, name='flag')
        return flag_service
