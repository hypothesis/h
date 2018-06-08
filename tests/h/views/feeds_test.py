# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.views.feeds import stream_atom, stream_rss


@pytest.mark.usefixtures(
    "fetch_ordered_annotations", "render_atom", "search_run", "routes"
)
class TestStreamAtom(object):
    def test_renders_atom(self, pyramid_request, render_atom):
        stream_atom(pyramid_request)

        render_atom.assert_called_once_with(
            request=pyramid_request,
            annotations=mock.sentinel.fetched_annotations,
            atom_url="http://example.com/thestream.atom",
            html_url="http://example.com/thestream",
            title="Some feed",
            subtitle="It contains stuff",
        )

    def test_returns_rendered_atom(self, pyramid_request, render_atom):
        result = stream_atom(pyramid_request)

        assert result == render_atom.return_value


@pytest.mark.usefixtures(
    "fetch_ordered_annotations", "render_rss", "search_run", "routes"
)
class TestStreamRSS(object):
    def test_renders_rss(self, pyramid_request, render_rss):
        stream_rss(pyramid_request)

        render_rss.assert_called_once_with(
            request=pyramid_request,
            annotations=mock.sentinel.fetched_annotations,
            rss_url="http://example.com/thestream.rss",
            html_url="http://example.com/thestream",
            title="Some feed",
            description="Stuff and things",
        )

    def test_returns_rendered_rss(self, pyramid_request, render_rss):
        result = stream_rss(pyramid_request)

        assert result == render_rss.return_value


@pytest.fixture
def fetch_ordered_annotations(patch):
    fetch_ordered_annotations = patch("h.views.feeds.fetch_ordered_annotations")
    fetch_ordered_annotations.return_value = mock.sentinel.fetched_annotations
    return fetch_ordered_annotations


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.stats = None
    return pyramid_request


@pytest.fixture
def pyramid_settings(pyramid_settings):
    settings = {}
    settings.update(pyramid_settings)
    settings.update(
        {
            "h.feed.title": "Some feed",
            "h.feed.subtitle": "It contains stuff",
            "h.feed.description": "Stuff and things",
        }
    )
    return settings


@pytest.fixture
def render_atom(patch):
    return patch("h.views.feeds.render_atom")


@pytest.fixture
def render_rss(patch):
    return patch("h.views.feeds.render_rss")


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("stream_atom", "/thestream.atom")
    pyramid_config.add_route("stream_rss", "/thestream.rss")
    pyramid_config.add_route("stream", "/thestream")


@pytest.fixture
def search(patch):
    return patch("h.views.feeds.search")


@pytest.fixture
def search_run(search):
    from h.search.core import SearchResult

    result = SearchResult(
        total=123, annotation_ids=["foo", "bar"], reply_ids=[], aggregations={}
    )
    search_run = search.Search.return_value.run
    search_run.return_value = result
    return search_run
