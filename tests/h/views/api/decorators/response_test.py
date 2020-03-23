# -*- coding: utf-8 -*-
from unittest import mock

import pytest
from pyramid.response import Response
from webob.acceptparse import create_accept_header

from h.views.api.decorators.response import version_media_type_header


class TestVersionMediaTypeHeader:
    def test_it_calls_wrapped_view_function(self, pyramid_request, testview):
        version_media_type_header("json")(testview)(None, pyramid_request)

        assert testview.called

    @pytest.mark.parametrize("subtype", ("json", "x-ndjson"))
    def test_it_sets_response_header_to_default_media_type_if_accept_not_set(
        self, pyramid_request, testview, subtype
    ):
        res = version_media_type_header(subtype)(testview)(None, pyramid_request)
        assert (
            res.headers["Hypothesis-Media-Type"]
            == f"application/vnd.hypothesis.v1+{subtype}"
        )

    @pytest.mark.parametrize(
        "accept,expected_header",
        [
            (
                "application/vnd.hypothesis.v2+json",
                "application/vnd.hypothesis.v2+json",
            ),
            (
                "application/vnd.hypothesis.v1+json",
                "application/vnd.hypothesis.v1+json",
            ),
            # application/json will be served by the default version of the API
            ("application/json", "application/vnd.hypothesis.v1+json"),
            # ditto for *
            ("*", "application/vnd.hypothesis.v1+json"),
        ],
    )
    def test_it_sets_response_header_based_on_value_of_accept(
        self, pyramid_request, testview, accept, expected_header
    ):
        pyramid_request.accept = create_accept_header(accept)

        res = version_media_type_header("json")(testview)(None, pyramid_request)

        assert res.headers["Hypothesis-Media-Type"] == expected_header


@pytest.fixture
def testview():
    return mock.Mock(return_value=Response("OK"))


@pytest.fixture
def pyramid_request(pyramid_request):
    # Set an empty accept on the request, imitating what pyramid does
    # in real life if no Accept header is set on the incoming request
    pyramid_request.accept = create_accept_header(None)
    return pyramid_request
