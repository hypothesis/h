# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import unicode_literals
import json

import unittest
import mock

import pyramid
from pyramid import testing
import pytest

from h import views
from h import api_client
from . import factories


class TestAnnotationView(unittest.TestCase):

    def test_og_document(self):
        context = {'id': '123', 'user': 'foo'}
        context['document'] = {'title': 'WikiHow — How to Make a  ☆Starmap☆'}
        request = testing.DummyRequest()
        result = views.annotation(context, request)
        assert isinstance(result, dict)
        test = lambda d: 'foo' in d['content'] and 'Starmap' in d['content']
        assert any(test(d) for d in result['meta_attrs'])

    def test_og_no_document(self):
        context = {'id': '123', 'user': 'foo'}
        request = testing.DummyRequest()
        result = views.annotation(context, request)
        assert isinstance(result, dict)
        test = lambda d: 'foo' in d['content']
        assert any(test(d) for d in result['meta_attrs'])


class TestJS(object):
    """Unit tests for the js() view callable."""

    def test_blocklist(self):
        """It should pass the blocklist as a string to embed.js."""
        request = mock.MagicMock()
        blocklist = {"foo": "bar"}
        request.registry.settings = {'h.blocklist': blocklist}

        data = views.js({}, request)

        assert data['blocklist'] == json.dumps(blocklist)


class TestValidateBlocklist(object):
    """Unit tests for the _validate_blocklist() function."""

    def test_valid(self):
        """It should load the setting into a dict."""
        blocklist = {
            "seanh.cc": {},
            "finance.yahoo.com": {},
            "twitter.com": {}
        }
        config = mock.MagicMock()
        config.registry.settings = {"h.blocklist": json.dumps(blocklist)}

        views._validate_blocklist(config)

        assert config.registry.settings["h.blocklist"] == blocklist, (
            "_validate_blocklist() should parse the JSON and turn it into a "
            "dict")

    def test_invalid_json(self):
        """It should raise ValueError if the setting is invalid."""
        config = mock.MagicMock()
        config.registry.settings = {"h.blocklist": "invalid"}

        with pytest.raises(ValueError):
            views._validate_blocklist(config)

    def test_default_value(self):
        """It should insert an empty dict if there's no setting."""
        config = mock.MagicMock()
        config.registry.settings = {}

        views._validate_blocklist(config)

        assert config.registry.settings["h.blocklist"] == {}


class TestStreamAtomView(object):

    """Unit tests for the stream_atom() view callable."""

    def test_it_returns_the_annotations_from_the_search_api(self):
        annotations = factories.Annotation.create_batch(10)
        request = mock.MagicMock()
        request.api_client.get.return_value = {"rows": annotations}

        data = views.stream_atom(request)

        assert data["annotations"] == annotations

    def test_it_returns_the_atom_url(self):
        """It returns the URL of the 'stream_atom' route as 'atom_url'.

        This is the URL to the Atom version of this Atom feed.

        """
        atom_url = "https://hypothes.is/stream.atom"
        request = mock.MagicMock()

        def side_effect(arg):
            return {"stream_atom": atom_url}.get(arg)

        request.route_url.side_effect = side_effect

        data = views.stream_atom(request)

        assert data["atom_url"] == atom_url

    def test_it_returns_the_stream_url(self):
        """It returns the URL of the 'stream' route as 'html_url'.

        This is the URL to the HTML page corresponding to this feed.

        """
        html_url = "https://hypothes.is/stream"
        request = mock.MagicMock()

        def side_effect(arg):
            return {"stream": html_url}.get(arg)

        request.route_url.side_effect = side_effect

        data = views.stream_atom(request)

        assert data["html_url"] == html_url

    def test_it_returns_the_feed_title(self):
        """It returns the 'h.feed.title' from the config as 'title'."""
        title = "Hypothesis Atom Feed"
        request = mock.MagicMock()

        def side_effect(arg):
            return {"h.feed.title": title}.get(arg)

        request.registry.settings.get.side_effect = side_effect

        data = views.stream_atom(request)

        assert data["title"] == title

    def test_it_returns_the_feed_subtitle(self):
        """It returns the 'h.feed.subtitle' from the config as 'subtitle'."""
        subtitle = "A feed of all our annotations"
        request = mock.MagicMock()

        def side_effect(arg):
            return {"h.feed.subtitle": subtitle}.get(arg)

        request.registry.settings.get.side_effect = side_effect

        data = views.stream_atom(request)

        assert data["subtitle"] == subtitle

    def test_it_adds_a_limit_param_if_none_is_given(self):
        request = mock.MagicMock()
        request.params = {}

        views.stream_atom(request)

        params = request.api_client.get.call_args[1]["params"]
        assert params["limit"] == 1000

    def test_it_forwards_user_supplied_limits(self):
        """User-supplied ``limit`` params should be forwarded.

        If the user supplies a ``limit`` param < 1000 this should be forwarded
        to the search API.

        """
        for limit in (0, 500, 1000):
            request = mock.MagicMock()
            request.params = {"limit": limit}

            views.stream_atom(request)

            params = request.api_client.get.call_args[1]["params"]
            assert params["limit"] == limit

    def test_it_ignores_limits_greater_than_1000(self):
        """It doesn't let the user specify a ``limit`` > 1000.

        It just reduces the limit to 1000.

        """
        request = mock.MagicMock()
        request.params = {"limit": 1001}

        views.stream_atom(request)

        params = request.api_client.get.call_args[1]["params"]
        assert params["limit"] == 1000

    def test_it_falls_back_to_1000_if_limit_is_invalid(self):
        """If the user gives an invalid limit value it falls back to 1000."""
        for limit in ("not a valid integer", None, [1, 2, 3]):
            request = mock.MagicMock()
            request.params = {"limit": limit}

            views.stream_atom(request)

            params = request.api_client.get.call_args[1]["params"]
            assert params["limit"] == 1000

    def test_it_falls_back_to_1000_if_limit_is_negative(self):
        """If given a negative number for limit it falls back to 1000."""
        request = mock.MagicMock()
        request.params = {"limit": -50}

        views.stream_atom(request)

        params = request.api_client.get.call_args[1]["params"]
        assert params["limit"] == 1000

    def test_it_forwards_url_params_to_the_api(self):
        """Any URL params are forwarded to the search API."""
        request = mock.MagicMock()
        request.params = {
            "user": "seanh",
            "tags": "JavaScript",
            "foo": "bar"
        }

        views.stream_atom(request)

        params = request.api_client.get.call_args[1]["params"]
        assert params["user"] == "seanh"
        assert params["tags"] == "JavaScript"
        assert params["foo"] == "bar"

    def test_it_raises_httpserviceunavailable_for_connectionerror(self):
        request = mock.MagicMock()
        request.api_client.get.side_effect = api_client.ConnectionError

        with pytest.raises(pyramid.httpexceptions.HTTPServiceUnavailable):
            views.stream_atom(request)

    def test_it_raises_httpgatewaytimeout_for_timeout(self):
        request = mock.MagicMock()
        request.api_client.get.side_effect = api_client.Timeout

        with pytest.raises(pyramid.httpexceptions.HTTPGatewayTimeout):
            views.stream_atom(request)

    def test_it_raises_httpbadgateway_for_apierror(self):
        request = mock.MagicMock()
        request.api_client.get.side_effect = api_client.APIError

        with pytest.raises(pyramid.httpexceptions.HTTPBadGateway):
            views.stream_atom(request)
