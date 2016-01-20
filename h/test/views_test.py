# -*- coding: utf-8 -*-
# pylint: disable=protected-access,no-self-use
from __future__ import unicode_literals
import json

import unittest
import mock
from mock import patch

from pyramid import testing
import pytest

from h import views


def _dummy_request():
    request = testing.DummyRequest()
    request.webassets_env = mock.MagicMock()
    request.route_url = mock.MagicMock()
    request.sentry = mock.MagicMock()
    return request


class TestAnnotationView(unittest.TestCase):

    @patch('h.client.render_app_html')
    def test_og_document(self, render_app_html):
        render_app_html.return_value = '<html></html>'
        annotation = {'id': '123', 'user': 'foo'}
        annotation['document'] = {'title': 'WikiHow — How to Make a  ☆Starmap☆'}
        context = mock.MagicMock(model=annotation)
        request = _dummy_request()
        views.annotation(context, request)
        args, kwargs = render_app_html.call_args
        test = lambda d: 'foo' in d['content'] and 'Starmap' in d['content']
        assert any(test(d) for d in kwargs['extra']['meta_attrs'])

    @patch('h.client.render_app_html')
    def test_og_no_document(self, render_app_html):
        render_app_html.return_value = '<html></html>'
        annotation = {'id': '123', 'user': 'foo'}
        context = mock.MagicMock(model=annotation)
        request = _dummy_request()
        views.annotation(context, request)
        args, kwargs = render_app_html.call_args
        test = lambda d: 'foo' in d['content']
        assert any(test(d) for d in kwargs['extra']['meta_attrs'])
