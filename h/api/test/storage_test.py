# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock
from mock import patch
from pyramid.testing import DummyRequest

from h import db
from h.api import storage
from h.api.models.annotation import Annotation


def test_fetch_annotation_elastic(postgres_enabled, ElasticAnnotation):
    postgres_enabled.return_value = False
    ElasticAnnotation.fetch.return_value = mock.Mock()

    actual = storage.fetch_annotation(DummyRequest(), '123')

    ElasticAnnotation.fetch.assert_called_once_with('123')
    assert ElasticAnnotation.fetch.return_value == actual


def test_fetch_annotation_postgres(postgres_enabled):
    request = DummyRequest(db=db.Session)
    postgres_enabled.return_value = True

    annotation = Annotation(userid='luke')
    db.Session.add(annotation)
    db.Session.flush()

    actual = storage.fetch_annotation(request, annotation.id)
    assert annotation == actual


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
    patcher = patch('h.api.models.elastic.Document', autospec=True)
    module = patcher.start()
    request.addfinalizer(patcher.stop)
    return module


@pytest.fixture
def postgres_enabled(request):
    patcher = patch('h.api.storage._postgres_enabled', autospec=True)
    func = patcher.start()
    request.addfinalizer(patcher.stop)
    return func


@pytest.fixture
def ElasticAnnotation(request):
    patcher = patch('h.api.storage.elastic.Annotation', autospec=True)
    cls = patcher.start()
    request.addfinalizer(patcher.stop)
    return cls
