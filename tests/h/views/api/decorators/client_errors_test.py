# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import mock
import pytest

from pyramid.response import Response

from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound

from h.views.api.decorators.client_errors import (
    NOT_FOUND_MESSAGE,
    unauthorized_to_not_found,
    not_found_reason,
)


class TestUnauthorizedToNotFound(object):
    def test_it_calls_wrapped_view_function(self, pyramid_request, testview):

        unauthorized_to_not_found(testview)(None, pyramid_request)

        assert testview.called

    def test_it_replaces_context_with_404_exception(self, pyramid_request, testview):
        wrapped = unauthorized_to_not_found(testview)

        wrapped(HTTPForbidden(), pyramid_request)

        context, _ = testview.call_args[0]

        assert isinstance(context, HTTPNotFound)

    def test_it_replaces_404_message(self, pyramid_request, testview):
        wrapped = unauthorized_to_not_found(testview)

        wrapped(HTTPNotFound(), pyramid_request)

        context, _ = testview.call_args[0]
        assert context.message == NOT_FOUND_MESSAGE


class TestNotFoundReason(object):
    def test_it_replaces_context_message(self, pyramid_request, testview):
        wrapped = not_found_reason(testview)

        wrapped(HTTPNotFound(), pyramid_request)

        context, _ = testview.call_args[0]
        assert context.message == NOT_FOUND_MESSAGE

    def test_it_does_not_replace_context_exception(self, pyramid_request, testview):
        wrapped = not_found_reason(testview)
        not_found = HTTPNotFound()

        wrapped(not_found, pyramid_request)

        context, _ = testview.call_args[0]
        assert context == not_found


@pytest.fixture
def testview():
    return mock.Mock(return_value=Response("OK"))
