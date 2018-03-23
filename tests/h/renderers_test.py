# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import OrderedDict

import mock
import pytest

from h.renderers import json_sorted_factory
from h.renderers import SVGRenderer


class TestSortedJSONRenderer(object):

    def test_sorts_response_keys(self):
        # An OrderedDict makes sure the keys won't end up in order by chance
        data = OrderedDict([('bar', 1), ('foo', 'bang'), ('baz', 5)])
        renderer = json_sorted_factory(info=None)

        result = renderer(data, system={})

        assert result == '{"bar": 1, "baz": 5, "foo": "bang"}'


class TestSVGRenderer(object):
    def test_it_sets_the_content_type(self, pyramid_request, system, svg_renderer):
        svg_renderer(mock.sentinel.svg_content, system)

        assert pyramid_request.response.content_type == 'image/svg+xml'

    def test_it_returns_the_svg_content(self, system, svg_renderer):
        # It returns the actual SVG content (u"<svg> ... </svg>") (actually
        # just whatever the view callable that's using the renderer returned)
        # as the body of the response for Pyramid to render.
        assert svg_renderer(mock.sentinel.svg_content, system) == mock.sentinel.svg_content

    @pytest.fixture
    def system(self, pyramid_request):
        """
        Return a fake Pyramid `system` dict.

        Returns a fake of the `system` dict that Pyramid passes to renderers
        when it calls them. It's a dict containing a bunch of Pyramid stuff,
        for example the current request.

        """
        return {
            'request': pyramid_request,
        }

    @pytest.fixture
    def svg_renderer(self):
        return SVGRenderer(mock.sentinel.info)
