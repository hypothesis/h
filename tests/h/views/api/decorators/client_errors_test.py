from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPForbidden, HTTPNotAcceptable, HTTPNotFound
from pyramid.response import Response
from webob.acceptparse import create_accept_header

from h.views.api.decorators.client_errors import (
    normalize_not_found,
    unauthorized_to_not_found,
    validate_media_types,
)


class TestUnauthorizedToNotFound:
    def test_it_calls_wrapped_view_function(self, pyramid_request, testview):
        unauthorized_to_not_found(testview)(None, pyramid_request)

        assert testview.called

    def test_it_replaces_context_with_404_exception(self, pyramid_request, testview):
        wrapped = unauthorized_to_not_found(testview)

        wrapped(HTTPForbidden(), pyramid_request)

        context, _ = testview.call_args[0]

        assert isinstance(context, HTTPNotFound)

    def test_it_sets_appropriate_404_message(self, pyramid_request, testview):
        wrapped = unauthorized_to_not_found(testview)

        wrapped(HTTPNotFound(), pyramid_request)

        context, _ = testview.call_args[0]
        assert context.message == (
            "Either the resource you requested doesn't exist,"
            " or you are not currently authorized to see it."
        )


class TestNormalizeNotFound:
    def test_it_sets_appropriate_message(self, pyramid_request, testview):
        wrapped = normalize_not_found(testview)

        wrapped(HTTPNotFound(), pyramid_request)

        context, _ = testview.call_args[0]
        assert context.message == (
            "Either the resource you requested doesn't exist,"
            " or you are not currently authorized to see it."
        )

    def test_context_is_not_found(self, pyramid_request, testview):
        wrapped = normalize_not_found(testview)

        # This view decorator would never have a reason to deal with
        # a 403 as a context, but it would be valid
        wrapped(HTTPForbidden(), pyramid_request)

        context, _ = testview.call_args[0]
        assert isinstance(context, HTTPNotFound)


class TestValidateMediaTypes:
    def test_it_calls_wrapped_view_function(self, pyramid_request, testview):
        validate_media_types(testview)(None, pyramid_request)

        assert testview.called

    def test_it_does_not_modify_context_if_accept_not_set(
        self, pyramid_request, testview
    ):
        fake_context = mock.Mock()
        validate_media_types(testview)(fake_context, pyramid_request)

        context, _ = testview.call_args[0]
        assert context == fake_context

    def test_it_does_not_modify_context_if_any_accept_values_ok(
        self, pyramid_request, testview
    ):
        # At least one of these is valid
        pyramid_request.accept = create_accept_header("application/json, foo/bar")
        fake_context = mock.Mock()
        validate_media_types(testview)(fake_context, pyramid_request)

        context, _ = testview.call_args[0]
        assert context == fake_context

    def test_it_replaces_context_with_406_if_accept_set_and_invalid(
        self, pyramid_request, testview
    ):
        # None of these is valid
        pyramid_request.accept = create_accept_header(
            "application/something+json, foo/bar"
        )
        fake_context = mock.Mock()
        validate_media_types(testview)(fake_context, pyramid_request)

        context, _ = testview.call_args[0]
        assert isinstance(context, HTTPNotAcceptable)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        # Set an empty accept on the request, imitating what pyramid does
        # in real life if no Accept header is set on the incoming request
        pyramid_request.accept = create_accept_header(None)
        return pyramid_request


@pytest.fixture
def testview():
    return mock.Mock(return_value=Response("OK"))
