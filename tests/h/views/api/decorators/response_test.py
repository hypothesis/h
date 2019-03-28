# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import mock
import pytest

from pyramid.response import Response
from webob.acceptparse import MIMENilAccept, MIMEAccept

from h.views.api.decorators.response import version_media_type_header


class TestVersionMediaTypeHeader(object):
    def test_it_calls_wrapped_view_function(self, pyramid_request, testview):
        version_media_type_header(testview)(None, pyramid_request)

        assert testview.called

    def test_it_sets_response_header_to_default_media_type_if_accept_not_set(
        self, pyramid_request, testview
    ):
        res = version_media_type_header(testview)(None, pyramid_request)
        assert (
            res.headers["Hypothesis-Media-Type"] == "application/vnd.hypothesis.v1+json"
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
        pyramid_request.accept = MIMEAccept(accept)

        res = version_media_type_header(testview)(None, pyramid_request)

        assert res.headers["Hypothesis-Media-Type"] == expected_header


@pytest.fixture
def testview():
    return mock.Mock(return_value=Response("OK"))


@pytest.fixture
def pyramid_request(pyramid_request):
    # Set an empty accept on the request, imitating what pyramid does
    # in real life if no Accept header is set on the incoming request
    pyramid_request.accept = MIMENilAccept()
    return pyramid_request
