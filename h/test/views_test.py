# -*- coding: utf-8 -*-
# pylint: disable=protected-access,no-self-use
from __future__ import unicode_literals
import json

import unittest
import mock

from pyramid import testing
import pytest

from h import views


class TestAnnotationView(unittest.TestCase):

    def test_og_document(self):
        annotation = {'id': '123', 'user': 'foo'}
        annotation['document'] = {'title': 'WikiHow — How to Make a  ☆Starmap☆'}
        context = mock.MagicMock(model=annotation)
        request = testing.DummyRequest()
        result = views.annotation(context, request)
        assert isinstance(result, dict)
        test = lambda d: 'foo' in d['content'] and 'Starmap' in d['content']
        assert any(test(d) for d in result['meta_attrs'])

    def test_og_no_document(self):
        annotation = {'id': '123', 'user': 'foo'}
        context = mock.MagicMock(model=annotation)
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

        data = views.embed({}, request)

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
