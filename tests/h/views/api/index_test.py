# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import testing
from pyramid.config import Configurator

from h.views.api import index as views


class TestIndex(object):
    def test_it_returns_the_right_links(self, pyramid_config, pyramid_request):

        # Scan `h.views.api_annotations` for API link metadata specified in @api_config
        # declarations.
        config = Configurator()
        config.scan("h.views.api.annotations")
        pyramid_request.registry.api_links = config.registry.api_links

        pyramid_config.add_route("api.search", "/dummy/search")
        pyramid_config.add_route("api.annotations", "/dummy/annotations")
        pyramid_config.add_route("api.annotation", "/dummy/annotations/:id")
        pyramid_config.add_route("api.links", "/dummy/links")

        result = views.index(testing.DummyResource(), pyramid_request)

        host = "http://example.com"  # Pyramid's default host URL'
        links = result["links"]
        assert links["annotation"]["create"]["method"] == "POST"
        assert links["annotation"]["create"]["url"] == (host + "/dummy/annotations")
        assert links["annotation"]["delete"]["method"] == "DELETE"
        assert links["annotation"]["delete"]["url"] == (host + "/dummy/annotations/:id")
        assert links["annotation"]["read"]["method"] == "GET"
        assert links["annotation"]["read"]["url"] == (host + "/dummy/annotations/:id")
        assert links["annotation"]["update"]["method"] == "PATCH"
        assert links["annotation"]["update"]["url"] == (host + "/dummy/annotations/:id")
        assert links["search"]["method"] == "GET"
        assert links["search"]["url"] == host + "/dummy/search"
