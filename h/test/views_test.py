# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
import mock

from pyramid import testing
import pytest

from h import views


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


class TestAtomStreamView(object):

    def test_validate_default_atom_stream_limit_fallback(self):
        """It should return 10 if there's no value in the config file."""
        settings = {}

        views._validate_default_atom_stream_limit(settings)

        assert settings[views._ATOM_STREAM_LIMIT_SETTINGS_KEY] == 10

    def test_validate_default_atom_stream_limit_invalid(self):
        """Should raise RuntimeError given an invalid value in settings."""
        for value in (None, "", -2, -23.7, "foo", True, False, [], {}):
            with pytest.raises(RuntimeError):
                views._validate_default_atom_stream_limit(
                    {views._ATOM_STREAM_LIMIT_SETTINGS_KEY: value})

    def test_validate_default_atom_stream_limit_int(self):
        settings = {views._ATOM_STREAM_LIMIT_SETTINGS_KEY: 5}

        views._validate_default_atom_stream_limit(settings)

        assert settings[views._ATOM_STREAM_LIMIT_SETTINGS_KEY] == 5

    def test_validate_default_atom_stream_limit_float(self):
        settings = {views._ATOM_STREAM_LIMIT_SETTINGS_KEY: 5.2}

        views._validate_default_atom_stream_limit(settings)

        assert settings[views._ATOM_STREAM_LIMIT_SETTINGS_KEY] == 5

    def test_validate_default_atom_stream_limit_string(self):
        settings = {views._ATOM_STREAM_LIMIT_SETTINGS_KEY: "11"}

        views._validate_default_atom_stream_limit(settings)

        assert settings[views._ATOM_STREAM_LIMIT_SETTINGS_KEY] == 11

    def test_atom_stream_limit_valid(self):
        request = mock.Mock()
        request.registry.settings = {views._ATOM_STREAM_LIMIT_SETTINGS_KEY: 10}
        request.params = {"limit": "7"}
        assert views._atom_stream_limit(request) == 7

    def test_atom_stream_limit_default(self):
        request = mock.Mock()
        request.registry.settings = {views._ATOM_STREAM_LIMIT_SETTINGS_KEY: 13}
        request.params = {}
        assert views._atom_stream_limit(request) == 13

    def test_atom_stream_limit_TypeError(self):
        request = mock.Mock()
        request.registry.settings = {views._ATOM_STREAM_LIMIT_SETTINGS_KEY: 13}
        for value in (None, True, False, [], {}):
            request.params = {"limit": value}
            with pytest.raises(TypeError):
                views._atom_stream_limit(request)

    def test_atom_stream_limit_ValueError(self):
        request = mock.Mock()
        request.registry.settings = {views._ATOM_STREAM_LIMIT_SETTINGS_KEY: 13}
        for value in ("", -2, -23.7, "foo"):
            request.params = {"limit": value}
            with pytest.raises(ValueError):
                views._atom_stream_limit(request)
