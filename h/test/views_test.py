# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest

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
