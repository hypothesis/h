# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import patch, MagicMock, PropertyMock
from pyramid import testing
import pytest

from h.api.models.annotation import Annotation
from h.api.models.document import Document
from h.views import main


def _dummy_request():
    request = testing.DummyRequest()
    request.assets_env = MagicMock()
    request.route_url = MagicMock()
    request.sentry = MagicMock()
    return request


@patch('h.client.render_app_html')
@pytest.mark.usefixtures('annotation_document', 'document_title')
def test_og_document(render_app_html, annotation_document, document_title):
    annotation = Annotation(id='123', userid='foo', target_uri='http://example.com')
    document = Document()
    annotation_document.return_value = document
    document_title.return_value = 'WikiHow — How to Make a ☆Starmap☆'

    render_app_html.return_value = '<html></html>'
    request = _dummy_request()
    main.annotation_page(annotation, request)
    args, kwargs = render_app_html.call_args
    test = lambda d: 'foo' in d['content'] and 'Starmap' in d['content']
    assert any(test(d) for d in kwargs['extra']['meta_attrs'])


@patch('h.client.render_app_html')
def test_og_no_document(render_app_html):
    annotation = Annotation(id='123', userid='foo', target_uri='http://example.com')

    render_app_html.return_value = '<html></html>'
    request = _dummy_request()
    main.annotation_page(annotation, request)
    args, kwargs = render_app_html.call_args
    test = lambda d: 'foo' in d['content']
    assert any(test(d) for d in kwargs['extra']['meta_attrs'])


@pytest.fixture
def annotation_document(patch):
    return patch('h.api.models.annotation.Annotation.document',
                 autospec=None,
                 new_callable=PropertyMock)


@pytest.fixture
def document_title(patch):
    return patch('h.api.models.document.Document.title',
                 autospec=None,
                 new_callable=PropertyMock)
