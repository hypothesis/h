from unittest.mock import sentinel

import pytest

from h.views.feeds import stream_atom, stream_rss


class TestStreamAtom:
    def test_it(self, render_atom, pyramid_request, annotation_read_service):
        result = stream_atom(pyramid_request)

        render_atom.assert_called_once_with(
            request=pyramid_request,
            annotations=annotation_read_service.get_annotations_by_id.return_value,
            atom_url="http://example.com/stream_atom",
            html_url="http://example.com/stream",
            title=sentinel.feed_title,
            subtitle=sentinel.feed_subtitle,
        )

        assert result == render_atom.return_value

    @pytest.fixture
    def render_atom(self, patch):
        return patch("h.views.feeds.render_atom")


class TestStreamRSS:
    def test_it(self, render_rss, pyramid_request, annotation_read_service):
        result = stream_rss(pyramid_request)

        render_rss.assert_called_once_with(
            request=pyramid_request,
            annotations=annotation_read_service.get_annotations_by_id.return_value,
            rss_url="http://example.com/stream_rss",
            html_url="http://example.com/stream",
            title=sentinel.feed_title,
            description=sentinel.feed_description,
        )

        assert result == render_rss.return_value

    @pytest.fixture
    def render_rss(self, patch):
        return patch("h.views.feeds.render_rss")


@pytest.fixture
def pyramid_settings(pyramid_settings):
    pyramid_settings["h.feed.title"] = sentinel.feed_title
    pyramid_settings["h.feed.subtitle"] = sentinel.feed_subtitle
    pyramid_settings["h.feed.description"] = sentinel.feed_description

    return pyramid_settings


@pytest.fixture(autouse=True)
def Search(patch):
    return patch("h.views.feeds.Search")


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    pyramid_config.add_route("stream_atom", "/stream_atom")
    pyramid_config.add_route("stream_rss", "/stream_rss")
    pyramid_config.add_route("stream", "/stream")
