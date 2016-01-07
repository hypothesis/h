# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from mock import patch

from h.api import storage


def test_expand_uri_no_document(document_model):
    document_model.get_by_uri.return_value = None
    assert storage.expand_uri("http://example.com/") == ["http://example.com/"]


def test_expand_uri_document_doesnt_expand_canonical_uris(document_model):
    document = document_model.get_by_uri.return_value
    document.get.return_value = [
        {"href": "http://foo.com/"},
        {"href": "http://bar.com/"},
        {"href": "http://example.com/", "rel": "canonical"},
    ]
    document.uris.return_value = [
        "http://foo.com/",
        "http://bar.com/",
        "http://example.com/",
    ]
    assert storage.expand_uri("http://example.com/") == ["http://example.com/"]


def test_expand_uri_document_uris(document_model):
    document_model.get_by_uri.return_value.uris.return_value = [
        "http://foo.com/",
        "http://bar.com/",
    ]
    assert storage.expand_uri("http://example.com/") == [
        "http://foo.com/",
        "http://bar.com/",
    ]


@pytest.fixture
def document_model(config, request):
    patcher = patch('h.api.models.Document', autospec=True)
    module = patcher.start()
    request.addfinalizer(patcher.stop)
    return module
