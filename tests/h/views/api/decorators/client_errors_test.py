# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import mock
import pytest

from pyramid.response import Response

from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPGone

from h.views.api.decorators.client_errors import client_error_decorator


class TestClientErrorDecorator(object):
    def test_it_calls_wrapped_view_function(self, pyramid_request, testview):

        client_error_decorator(testview)(None, pyramid_request)

        assert testview.called

    def test_it_replaces_403s_with_404s(self, pyramid_request, testview):
        wrapped = client_error_decorator(testview)

        wrapped(HTTPForbidden(), pyramid_request)

        (context, _) = testview.call_args[0]

        assert isinstance(context, HTTPNotFound)

    def test_it_replaces_404_message(self, pyramid_request, testview):
        wrapped = client_error_decorator(testview)
        default_not_found = HTTPNotFound()

        wrapped(HTTPNotFound(), pyramid_request)

        (context, _) = testview.call_args[0]
        assert context.message != default_not_found.message

    def test_it_does_not_replace_other_http_4xx_messages(
        self, pyramid_request, testview
    ):
        wrapped = client_error_decorator(testview)
        default_gone = HTTPGone()

        wrapped(HTTPGone(), pyramid_request)

        (context, _) = testview.call_args[0]
        assert context.message == default_gone.message

    @pytest.fixture
    def testview(self):
        return mock.Mock(return_value=Response("OK"))
