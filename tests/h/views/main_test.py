# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from memex.models.annotation import Annotation
from memex.models.document import Document
from h.views import main



@mock.patch('h.client.render_app_html')
@pytest.mark.usefixtures('routes')
def test_og_document(render_app_html, annotation_document, document_title, pyramid_request):
    annotation = Annotation(id='123', userid='foo', target_uri='http://example.com')
    document = Document()
    annotation_document.return_value = document
    document_title.return_value = 'WikiHow — How to Make a ☆Starmap☆'

    render_app_html.return_value = '<html></html>'
    main.annotation_page(annotation, pyramid_request)
    args, kwargs = render_app_html.call_args
    test = lambda d: 'foo' in d['content'] and 'Starmap' in d['content']
    assert any(test(d) for d in kwargs['extra']['meta_attrs'])


@mock.patch('h.client.render_app_html')
@pytest.mark.usefixtures('routes')
def test_og_no_document(render_app_html, pyramid_request):
    annotation = Annotation(id='123', userid='foo', target_uri='http://example.com')

    render_app_html.return_value = '<html></html>'
    main.annotation_page(annotation, pyramid_request)
    args, kwargs = render_app_html.call_args
    test = lambda d: 'foo' in d['content']
    assert any(test(d) for d in kwargs['extra']['meta_attrs'])


@pytest.fixture
def annotation_document(patch):
    return patch('memex.models.annotation.Annotation.document',
                 autospec=None,
                 new_callable=mock.PropertyMock)


@pytest.fixture
def document_title(patch):
    return patch('memex.models.document.Document.title',
                 autospec=None,
                 new_callable=mock.PropertyMock)


@pytest.fixture
def pyramid_config(pyramid_config):
    # Pretend the client assets environment has been configured
    pyramid_config.registry['assets_client_env'] = mock.Mock()
    return pyramid_config


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('api.annotation', '/api/ann/{id}')
    pyramid_config.add_route('api.index', '/api/index')
    pyramid_config.add_route('index', '/index')
