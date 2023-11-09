from unittest import mock

import pytest
from pyramid.response import Response

from h.feeds import render


@pytest.mark.usefixtures("render_to_response")
class TestRenderAtom:
    def test_it_sets_response_content_type(self, pyramid_request):
        response = render.render_atom(
            request=pyramid_request,
            annotations=[],
            atom_url="",
            html_url="",
            title="",
            subtitle="",
        )
        assert response.content_type == "application/atom+xml"


@pytest.mark.usefixtures("render_to_response")
class TestRenderRSS:
    def test_it_sets_response_content_type(self, pyramid_request):
        response = render.render_rss(
            request=pyramid_request,
            annotations=[],
            rss_url="",
            html_url="",
            title="",
            description="",
        )
        assert response.content_type == "application/rss+xml"


@pytest.fixture
def render_to_response(patch):
    response = mock.Mock(spec_set=Response)
    func = patch("h.feeds.render.renderers.render_to_response")
    func.return_value = response
    return func
