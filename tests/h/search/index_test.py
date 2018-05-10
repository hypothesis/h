# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from h import search


class TestIndex(object):
    def test_it_can_index_an_annotation_with_no_document(self, factories,
                                                         index, get):
        annotation = factories.Annotation.build(id="test_annotation_id",
                                                document=None)

        index(annotation)

        assert get(annotation.id)["document"] == {}

    def test_it_indexes_the_annotations_document_web_uri(self, factories,
                                                       index, get):
        annotation = factories.Annotation.build(
            id="test_annotation_id",
            document=factories.Document.build(web_uri="https://example.com/example_article"),
        )

        index(annotation)

        # *Searching* for an annotation by ``annotation.document`` (e.g. by
        # document ``title`` or ``web_uri``) isn't enabled.  But you can
        # retrieve an annotation by ID, or by searching on other field(s), and
        # then access its ``document``. Bouncer
        # (https://github.com/hypothesis/bouncer) accesses h's Elasticsearch
        # index directly and uses this ``document`` field.
        assert get(annotation.id)["document"]["web_uri"] == "https://example.com/example_article"

    def test_it_can_index_an_annotation_with_a_document_with_no_web_uri(self, factories,
                                                                        index, get):
        annotation = factories.Annotation.build(
            id="test_annotation_id",
            document=factories.Document.build(web_uri=None),
        )

        index(annotation)

        assert "web_uri" not in get(annotation.id)["document"]

    def test_it_indexes_the_annotations_document_title(self, factories,
                                                       index, get):
        annotation = factories.Annotation.build(
            id="test_annotation_id",
            document=factories.Document.build(title="test_document_title"),
        )

        index(annotation)

        assert get(annotation.id)["document"]["title"] == ["test_document_title"]

    def test_it_can_index_an_annotation_with_a_document_with_no_title(self, factories,
                                                                      index, get):
        annotation = factories.Annotation.build(
            id="test_annotation_id",
            document=factories.Document.build(title=None),
        )

        index(annotation)

        assert "title" not in get(annotation.id)["document"]

    @pytest.fixture
    def index(self, es_client, pyramid_request):
        def _index(annotation):
            """Index the given annotation into Elasticsearch."""
            search.index.index(es_client, annotation, pyramid_request)
        return _index

    @pytest.fixture
    def get(self, es_client):
        def _get(annotation_id):
            """Return the annotation with the given ID from Elasticsearch."""
            return es_client.conn.get(
                index=es_client.index, doc_type="annotation",
                id=annotation_id)["_source"]
        return _get
