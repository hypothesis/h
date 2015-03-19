# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
import mock

from pyramid import testing

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

    def test_validate_limit_with_valid_url_param(self):
        request = mock.Mock()
        request.registry.settings = {"h.stream.atom.limit": 10}
        request.params = {"limit": 3}

        limit = views._atom_stream_validate_limit(request)

        assert limit == 3

    def test_validate_limit_with_invalid_url_param_and_no_default(self):
        request = mock.Mock()
        request.registry.settings = {}
        request.params = {"limit": "foo"}

        limit = views._atom_stream_validate_limit(request)

        assert limit == 10

    def test_validate_limit_with_invalid_url_param_and_valid_default(self):
        request = mock.Mock()
        request.registry.settings = {"h.stream.atom.limit": 15}
        request.params = {"limit": "foo"}

        limit = views._atom_stream_validate_limit(request)

        assert limit == 15

    def test_validate_limit_with_invalid_url_param_and_invalid_default(self):
        request = mock.Mock()
        request.registry.settings = {"h.stream.atom.limit": "bar"}
        request.params = {"limit": "foo"}

        limit = views._atom_stream_validate_limit(request)

        assert limit == 10

    def test_validate_limit_with_no_url_param_and_no_default(self):
        request = mock.Mock()
        request.registry.settings = {}
        request.params = {}

        limit = views._atom_stream_validate_limit(request)

        assert limit == 10

    def test_validate_limit_with_no_url_param_and_valid_default(self):
        request = mock.Mock()
        request.registry.settings = {"h.stream.atom.limit": "3"}
        request.params = {}

        limit = views._atom_stream_validate_limit(request)

        assert limit == 3

    def test_validate_limit_with_no_url_param_and_invalid_default(self):
        request = mock.Mock()
        request.registry.settings = {"h.stream.atom.limit": "bar"}
        request.params = {}

        limit = views._atom_stream_validate_limit(request)

        assert limit == 10
