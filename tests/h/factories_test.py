# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
"""Unit tests for h/test/factories.py."""
import datetime

from h import db
from tests import factories


class TestDocument(object):

    def test_with_default_values(self):
        document = factories.Document()

        db.Session.flush()
        assert document.id
        assert isinstance(document.created, datetime.datetime)
        assert isinstance(document.updated, datetime.datetime)


class TestDocumentMeta(object):

    def test_with_default_values(self):
        document_meta = factories.DocumentMeta()

        db.Session.flush()
        assert document_meta.id
        assert document_meta.claimant
        assert document_meta.claimant_normalized
        assert document_meta.type
        assert document_meta.document
        assert document_meta.value
        assert isinstance(document_meta.created, datetime.datetime)
        assert isinstance(document_meta.updated, datetime.datetime)

    def test_with_custom_values(self):
        kwargs = dict(
            claimant='http://www.example.com/claimant',
            type='test_type',
            value='test_value',
        )

        document_meta = factories.DocumentMeta(**kwargs)

        for key, value in kwargs.items():
            assert getattr(document_meta, key) == value


class TestDocumentURI(object):

    def test_with_default_values(self):
        document_uri = factories.DocumentURI()

        db.Session.flush()
        assert document_uri.id
        assert document_uri.claimant
        assert document_uri.claimant_normalized
        assert document_uri.uri
        assert document_uri.uri_normalized
        assert document_uri.type
        assert document_uri.content_type
        assert document_uri.document
        assert isinstance(document_uri.created, datetime.datetime)
        assert isinstance(document_uri.updated, datetime.datetime)

    def test_with_custom_values(self):
        kwargs = dict(
            claimant='http://example.com/claimant',
            uri='http://example.com/uri',
            type='test_type',
            content_type='test_content_type',
        )

        document_uri = factories.DocumentURI(**kwargs)

        for key, value in kwargs.items():
            assert getattr(document_uri, key) == value


class TestAnnotation(object):

    def test_with_default_values(self):
        annotation = factories.Annotation()

        assert isinstance(annotation.tags, list)
        assert annotation.target_uri
        assert annotation.text
        assert annotation.userid
        assert annotation.target_selectors
        assert annotation.document
        assert annotation.document.title
        assert annotation.document.document_uris
        assert annotation.document.meta
        assert annotation.id
        assert isinstance(annotation.created, datetime.datetime)
        assert isinstance(annotation.updated, datetime.datetime)
        assert annotation.groupid
        assert isinstance(annotation.shared, bool)
        assert isinstance(annotation.references, list)
        assert isinstance(annotation.extra, dict)

    def test_with_custom_values(self):
        kwargs = dict(
            tags=['foo', 'bar'],
            target_uri='http://example.com/target_uri',
            userid='catalina',
            target_selectors=[{'foo': 'bar'}],
        )

        annotation = factories.Annotation(**kwargs)

        for key, value in kwargs.items():
            assert getattr(annotation, key) == value
