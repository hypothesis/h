# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import mock
import pytest

from pyramid.response import Response


from h.views.api.decorators.response import version_media_type_header


class TestVersionMediaTypeHeader(object):
    def test_it_calls_wrapped_view_function(self, pyramid_request, testview):
        version_media_type_header(testview)(None, pyramid_request)

        assert testview.called

    def test_it_sets_response_header_to_default_media_type(
        self, pyramid_request, testview, media_type_for_version
    ):
        res = version_media_type_header(testview)(None, pyramid_request)
        assert (
            res.headers["Hypothesis-Media-Type"] == media_type_for_version.return_value
        )


@pytest.fixture
def media_type_for_version(patch):
    return patch("h.views.api.decorators.response.media_type_for_version")


@pytest.fixture
def testview():
    return mock.Mock(return_value=Response("OK"))
