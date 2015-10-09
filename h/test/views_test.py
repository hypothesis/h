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
