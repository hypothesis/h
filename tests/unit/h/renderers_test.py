from collections import OrderedDict
from unittest import mock

import pytest

from h.renderers import SVGRenderer, json_sorted_factory


class TestSortedJSONRenderer:
    def test_sorts_response_keys(self):
        # An OrderedDict makes sure the keys won't end up in order by chance
        data = OrderedDict([("bar", 1), ("foo", "bang"), ("baz", 5)])
        renderer = json_sorted_factory(info=None)

        result = renderer(data, system={})

        assert result == '{"bar": 1, "baz": 5, "foo": "bang"}'


class TestSVGRenderer:
    def test_it_sets_the_content_type(self, pyramid_request, system, svg_renderer):
        svg_renderer(mock.sentinel.svg_content, system)

        assert pyramid_request.response.content_type == "image/svg+xml"

    def test_it_returns_the_svg_content(self, system, svg_renderer):
        # It returns the actual SVG content (u"<svg> ... </svg>") (actually
        # just whatever the view callable that's using the renderer returned)
        # as the body of the response for Pyramid to render.
        assert (
            svg_renderer(mock.sentinel.svg_content, system) == mock.sentinel.svg_content
        )

    def test_it_adds_a_vary_accept_encoding_header(
        self, pyramid_request, system, svg_renderer
    ):
        svg_renderer(mock.sentinel.svg_content, system)

        assert pyramid_request.response.headers.get("Vary") == "Accept-Encoding"

    def test_it_appends_accept_encoding_to_an_existing_vary_header(
        self, pyramid_request, system, svg_renderer
    ):
        # If something earlier in request processing has already added a Vary
        # header it should append Accept-Encoding to the existing Vary header,
        # and not for example replace the existing header with just
        # Accept-Encoding.
        pyramid_request.response.vary = ("User-Agent",)

        svg_renderer(mock.sentinel.svg_content, system)

        assert (
            pyramid_request.response.headers.get("Vary")
            == "User-Agent, Accept-Encoding"
        )

    def test_it_doesnt_add_duplicate_accept_encoding_values(
        self, pyramid_request, system, svg_renderer
    ):
        # If something earlier in request processing has already added
        # Accept-Encoding to the Vary header then it shouldn't add a second
        # Accept-Encoding to the header.
        pyramid_request.response.vary = ("User-Agent", "Accept-Encoding")

        svg_renderer(mock.sentinel.svg_content, system)

        assert (
            pyramid_request.response.headers.get("Vary")
            == "User-Agent, Accept-Encoding"
        )

    @pytest.fixture
    def system(self, pyramid_request):
        """
        Return a fake Pyramid `system` dict.

        Returns a fake of the `system` dict that Pyramid passes to renderers
        when it calls them. It's a dict containing a bunch of Pyramid stuff,
        for example the current request.

        """
        return {"request": pyramid_request}

    @pytest.fixture
    def svg_renderer(self):
        return SVGRenderer(mock.sentinel.info)
