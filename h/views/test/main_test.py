# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
from pyramid import testing

from h.views import main


def _dummy_request():
    request = testing.DummyRequest()
    request.webassets_env = mock.MagicMock()
    request.route_url = mock.MagicMock()
    request.sentry = mock.MagicMock()
    return request


@mock.patch('h.client.render_app_html')
def test_og_document(render_app_html):
    render_app_html.return_value = '<html></html>'
    annotation = {'id': '123', 'user': 'foo'}
    annotation['document'] = {'title': 'WikiHow — How to Make a  ☆Starmap☆'}
    request = _dummy_request()
    main.annotation_page(annotation, request)
    args, kwargs = render_app_html.call_args
    test = lambda d: 'foo' in d['content'] and 'Starmap' in d['content']
    assert any(test(d) for d in kwargs['extra']['meta_attrs'])


@mock.patch('h.client.render_app_html')
def test_og_no_document(render_app_html):
    render_app_html.return_value = '<html></html>'
    annotation = {'id': '123', 'user': 'foo'}
    request = _dummy_request()
    main.annotation_page(annotation, request)
    args, kwargs = render_app_html.call_args
    test = lambda d: 'foo' in d['content']
    assert any(test(d) for d in kwargs['extra']['meta_attrs'])
