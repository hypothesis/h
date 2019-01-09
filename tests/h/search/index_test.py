# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import elasticsearch
import elasticsearch_dsl
import logging
import mock
import pytest

import h.search.index

from tests.common.matchers import Matcher


@pytest.mark.usefixtures("annotations")
class TestIndex(object):
    def test_annotation_ids_are_used_as_elasticsearch_ids(
        self, es_client, factories, index
    ):
        annotation = factories.Annotation.build()

        index(annotation)

        result = es_client.conn.get(
            index=es_client.index, doc_type=es_client.mapping_type, id=annotation.id
        )
        assert result["_id"] == annotation.id

    def test_it_indexes_presented_annotation(
        self,
        factories,
        get_indexed_ann,
        index,
        pyramid_request,
        AnnotationSearchIndexPresenter,
    ):
        annotation = factories.Annotation.build()
        presenter = AnnotationSearchIndexPresenter.return_value
        presenter.asdict.return_value = {
            "id": annotation.id,
            "some_other_field": "a_value",
        }

        index(annotation)
        indexed_ann = get_indexed_ann(annotation.id)

        AnnotationSearchIndexPresenter.assert_called_once_with(
            annotation, pyramid_request
        )
        assert indexed_ann == presenter.asdict.return_value

    def test_it_can_index_an_annotation_with_no_document(
        self, factories, index, get_indexed_ann
    ):
        annotation = factories.Annotation.build(document=None)

        index(annotation)

        assert get_indexed_ann(annotation.id)["document"] == {}

    def test_it_indexes_the_annotations_document_web_uri(
        self, factories, index, get_indexed_ann
    ):
        annotation = factories.Annotation.build(
            document=factories.Document.build(
                web_uri="https://example.com/example_article"
            )
        )

        index(annotation)

        # *Searching* for an annotation by ``annotation.document`` (e.g. by
        # document ``title`` or ``web_uri``) isn't enabled.  But you can
        # retrieve an annotation by ID, or by searching on other field(s), and
        # then access its ``document``. Bouncer
        # (https://github.com/hypothesis/bouncer) accesses h's Elasticsearch
        # index directly and uses this ``document`` field.
        assert (
            get_indexed_ann(annotation.id)["document"]["web_uri"]
            == "https://example.com/example_article"
        )

    def test_it_can_index_an_annotation_with_a_document_with_no_web_uri(
        self, factories, index, get_indexed_ann
    ):
        annotation = factories.Annotation.build(
            document=factories.Document.build(web_uri=None)
        )

        index(annotation)

        assert "web_uri" not in get_indexed_ann(annotation.id)["document"]

    def test_it_indexes_the_annotations_document_title(
        self, factories, index, get_indexed_ann
    ):
        annotation = factories.Annotation.build(
            document=factories.Document.build(title="test_document_title")
        )

        index(annotation)

        assert get_indexed_ann(annotation.id)["document"]["title"] == [
            "test_document_title"
        ]

    def test_it_can_index_an_annotation_with_a_document_with_no_title(
        self, factories, index, get_indexed_ann
    ):
        annotation = factories.Annotation.build(
            document=factories.Document.build(title=None)
        )

        index(annotation)

        assert "title" not in get_indexed_ann(annotation.id)["document"]

    def test_it_notifies(
        self,
        AnnotationTransformEvent,
        factories,
        pyramid_request,
        notify,
        index,
        search,
    ):
        annotation = factories.Annotation.build(userid="acct:someone@example.com")

        index(annotation)

        event = AnnotationTransformEvent.return_value

        AnnotationTransformEvent.assert_called_once_with(
            pyramid_request, annotation, mock.ANY
        )
        notify.assert_called_once_with(event)

    def test_you_can_filter_annotations_by_authority(self, factories, index, search):
        annotation = factories.Annotation.build(userid="acct:someone@example.com")

        index(annotation)

        response = search.filter("term", authority="example.com").execute()
        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_creation_time(
        self, factories, index, search
    ):
        before = datetime.datetime.now()
        annotation = factories.Annotation.build()

        index(annotation)

        response = search.filter("range", created={"gte": before}).execute()
        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_updated_time(self, factories, index, search):
        update_time = datetime.datetime.now()
        annotation = factories.Annotation.build(
            id="test_annotation_id", updated=update_time
        )

        index(annotation)

        response = search.filter("range", updated={"gte": update_time}).execute()
        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_id(self, factories, index, search):
        annotation = factories.Annotation.build(id="test_ann_id")

        index(annotation)

        response = search.filter("term", id="test_ann_id").execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    @pytest.mark.parametrize(
        "user_search_str",
        ["acct:someone@example.com", "someone", "someone@example.com"],
    )
    def test_you_can_filter_annotations_by_user(
        self, factories, index, search, user_search_str
    ):
        annotation = factories.Annotation.build(userid="acct:someone@example.com")

        index(annotation)

        response = search.filter("term", user=user_search_str).execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_make_aggregations_on_user_raw(self, factories, index, search):
        annotation_1 = factories.Annotation.build(userid="acct:someone@example.com")
        annotation_2 = factories.Annotation.build(userid="acct:Someone@example.com")

        index(annotation_1, annotation_2)

        user_aggregation = elasticsearch_dsl.A("terms", field="user_raw")
        search.aggs.bucket("user_raw_terms", user_aggregation)

        response = search.execute()

        user_bucket_1 = next(
            bucket
            for bucket in response.aggregations.user_raw_terms.buckets
            if bucket["key"] == "acct:someone@example.com"
        )
        user_bucket_2 = next(
            bucket
            for bucket in response.aggregations.user_raw_terms.buckets
            if bucket["key"] == "acct:Someone@example.com"
        )

        assert user_bucket_1["doc_count"] == 1
        assert user_bucket_2["doc_count"] == 1

    def test_you_can_filter_annotations_by_tags(self, factories, index, search):
        annotation = factories.Annotation.build(
            id="test_annotation_id", tags=["ญหฬ", "tag"]
        )

        index(annotation)

        response1 = search.filter("terms", tags=["ญหฬ"]).execute()
        response2 = search.filter("terms", tags=["tag"]).execute()

        assert SearchResponseWithIDs([annotation.id]) == response1
        assert SearchResponseWithIDs([annotation.id]) == response2

    def test_you_can_make_aggregations_on_tags_raw(self, factories, index, search):
        annotation_1 = factories.Annotation.build(
            id="test_annotation_id_1", tags=["Hello"]
        )
        annotation_2 = factories.Annotation.build(
            id="test_annotation_id_2", tags=["hello"]
        )

        index(annotation_1, annotation_2)

        tags_aggregation = elasticsearch_dsl.A("terms", field="tags_raw")
        search.aggs.bucket("tags_raw_terms", tags_aggregation)

        response = search.execute()

        tag_bucket_1 = next(
            bucket
            for bucket in response.aggregations.tags_raw_terms.buckets
            if bucket["key"] == "Hello"
        )
        tag_bucket_2 = next(
            bucket
            for bucket in response.aggregations.tags_raw_terms.buckets
            if bucket["key"] == "hello"
        )

        assert tag_bucket_1["doc_count"] == 1
        assert tag_bucket_2["doc_count"] == 1

    def test_you_can_filter_annotations_by_uri(self, factories, index, search):
        my_uri = "http://example.com/anything/i/like?ex=something"
        annotation = factories.Annotation.build(
            id="test_annotation_id", target_uri=my_uri
        )

        index(annotation)

        response = search.filter("term", uri="example.com/anything/i/like").execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_text(self, factories, index, search):
        annotation = factories.Annotation.build(
            id="test_annotation_id", text="text to search"
        )

        index(annotation)

        response = search.filter("term", text="text").execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_unicode_text(self, factories, index, search):
        annotation = factories.Annotation.build(
            id="test_annotation_id", text="test ลข ญหฬ"
        )

        index(annotation)

        response = search.filter("term", text="ลข").execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_group(self, factories, index, search):
        annotation = factories.Annotation.build(
            id="test_annotation_id", groupid="some_group"
        )

        index(annotation)

        response = search.filter("term", group="some_group").execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_shared(self, factories, index, search):
        annotation = factories.Annotation.build(id="test_annotation_id", shared=False)

        index(annotation)

        response = search.filter("term", shared=False).execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_thread_ids(self, factories, index, search):
        annotation1 = factories.Annotation.build(id="test_annotation_id1")
        annotation2 = factories.Annotation.build(
            id="test_annotation_id2", thread=[annotation1]
        )

        index(annotation1, annotation2)

        response = search.filter("terms", thread_ids=[annotation1.id]).execute()

        assert SearchResponseWithIDs([annotation2.id]) == response

    def test_you_can_filter_annotations_by_hidden(
        self, AnnotationSearchIndexPresenter, factories, index, search
    ):
        annotation1 = factories.Annotation.build()
        annotation2 = factories.Annotation.build()

        presenter = AnnotationSearchIndexPresenter.return_value
        presenter.asdict.return_value = {"id": annotation1.id, "hidden": True}

        index(annotation1)

        presenter = AnnotationSearchIndexPresenter.return_value
        presenter.asdict.return_value = {"id": annotation2.id, "hidden": False}

        index(annotation2)

        response = search.filter("term", hidden=True).execute()

        assert SearchResponseWithIDs([annotation1.id]) == response

    @pytest.mark.parametrize(
        "quote,query",
        [
            ("It is a truth universally acknowledged", "truth"),
            ("यह एक सत्य सार्वभौमिक रूप से स्वीकार किया जाता है", "सत्य"),
            ("quick brown fox", "QUICK"),
        ],
    )
    def test_you_can_search_within_the_quote(
        self, factories, index, search, quote, query
    ):
        """Verify that the "TextQuoteSelector" selector is indexed as the "quote" field."""
        quote_selector = {
            "type": "TextQuoteSelector",
            "exact": quote,
            "prefix": "something before ",
            "suffix": " something after",
        }
        selectors = [quote_selector]
        annotation = factories.Annotation.build(target_selectors=selectors)

        index(annotation)

        response = search.query("match", quote=query)
        assert SearchResponseWithIDs([annotation.id]) == response

    @pytest.fixture
    def annotations(self, factories, index):
        """
        Add some annotations to Elasticsearch as "noise".

        These are annotations that we *don't* expect to show up in search
        results. We want some noise in the search index to make sure that the
        test search queries are only returning the expected annotations and
        not, for example, simply returning *all* annotations.

        """
        index(
            factories.Annotation.build(),
            factories.Annotation.build(),
            factories.Annotation.build(),
        )


class TestDelete(object):
    def test_annotation_is_marked_deleted(
        self, es_client, factories, get_indexed_ann, index
    ):
        annotation = factories.Annotation.build(id="test_annotation_id")

        index(annotation)

        assert "deleted" not in get_indexed_ann(annotation.id)

        h.search.index.delete(es_client, annotation.id)
        assert get_indexed_ann(annotation.id).get("deleted") is True


class TestBatchIndexer(object):
    def test_it_indexes_all_annotations(
        self, batch_indexer, factories, get_indexed_ann
    ):
        annotations = factories.Annotation.create_batch(3)
        ids = [a.id for a in annotations]

        batch_indexer.index()

        for _id in ids:
            assert get_indexed_ann(_id) is not None

    def test_it_indexes_specific_annotations(
        self, batch_indexer, factories, get_indexed_ann
    ):
        annotations = factories.Annotation.create_batch(5)
        ids = [a.id for a in annotations]
        ids_to_index = ids[:3]
        ids_not_to_index = ids[3:]

        batch_indexer.index(ids_to_index)

        for _id in ids_to_index:
            assert get_indexed_ann(_id) is not None

        for _id in ids_not_to_index:
            with pytest.raises(elasticsearch.exceptions.NotFoundError):
                get_indexed_ann(_id)

    def test_it_does_not_index_deleted_annotations(
        self, batch_indexer, factories, get_indexed_ann
    ):
        ann = factories.Annotation()
        # create deleted annotations
        ann_del = factories.Annotation(deleted=True)

        batch_indexer.index()

        assert get_indexed_ann(ann.id) is not None

        with pytest.raises(elasticsearch.exceptions.NotFoundError):
            get_indexed_ann(ann_del.id)

    def test_it_notifies(
        self,
        AnnotationSearchIndexPresenter,
        AnnotationTransformEvent,
        batch_indexer,
        factories,
        pyramid_request,
        notify,
    ):
        annotations = factories.Annotation.create_batch(3)

        batch_indexer.index()

        event = AnnotationTransformEvent.return_value

        for annotation in annotations:
            AnnotationTransformEvent.assert_has_calls(
                [
                    mock.call(
                        pyramid_request,
                        annotation,
                        AnnotationSearchIndexPresenter.return_value.asdict.return_value,
                    )
                ]
            )
            notify.assert_has_calls([mock.call(event)])

    def test_it_logs_indexing_status(self, caplog, batch_indexer, factories):
        num_annotations = 10
        window_size = 3
        num_index_records = 0
        annotations = factories.Annotation.create_batch(num_annotations)
        ids = [a.id for a in annotations]

        with caplog.at_level(logging.INFO):
            batch_indexer.index(ids, window_size)

        for record in caplog.records:
            if record.filename == "index.py":
                num_index_records = num_index_records + 1
                assert "indexed 0k annotations, rate=" in record.msg
        assert num_index_records == num_annotations // window_size

    def test_it_correctly_indexes_fields_for_bulk_actions(
        self, batch_indexer, es_client, factories, get_indexed_ann
    ):
        annotations = factories.Annotation.create_batch(2, groupid="group_a")

        batch_indexer.index()

        for ann in annotations:
            result = get_indexed_ann(ann.id)
            assert result.get("group") == ann.groupid
            assert result.get("authority") == ann.authority
            assert result.get("user") == ann.userid
            assert result.get("uri") == ann.target_uri

    def test_it_returns_errored_annotation_ids(self, batch_indexer, factories):
        annotations = factories.Annotation.create_batch(3)
        expected_errored_ids = set([annotations[0].id, annotations[2].id])

        elasticsearch.helpers.streaming_bulk = mock.Mock()
        elasticsearch.helpers.streaming_bulk.return_value = [
            (False, {"index": {"error": "some error", "_id": annotations[0].id}}),
            (True, {}),
            (False, {"index": {"error": "some error", "_id": annotations[2].id}}),
        ]

        errored = batch_indexer.index()

        assert errored == expected_errored_ids

    def test_it_does_not_error_if_annotations_already_indexed(
        self, db_session, es_client, factories, pyramid_request
    ):
        annotations = factories.Annotation.create_batch(3)
        expected_errored_ids = set([annotations[1].id])

        elasticsearch.helpers.streaming_bulk = mock.Mock()
        elasticsearch.helpers.streaming_bulk.return_value = [
            (True, {}),
            (False, {"create": {"error": "some error", "_id": annotations[1].id}}),
            (
                False,
                {
                    "create": {
                        "error": "document already exists",
                        "_id": annotations[2].id,
                    }
                },
            ),
        ]

        errored = h.search.index.BatchIndexer(
            db_session, es_client, pyramid_request, es_client.index, "create"
        ).index()

        assert errored == expected_errored_ids


class SearchResponseWithIDs(Matcher):
    """
    Matches an elasticsearch_dsl response with the given annotation ids.

    Matches any :py:class:`elasticsearch_dsl.result.Response` search
    response object whose search results are exactly the annotations with
    the given ids, in the given order.

    """

    def __init__(self, annotation_ids):
        self.annotation_ids = annotation_ids

    def __eq__(self, search_response):
        ids = [search_result.meta["id"] for search_result in search_response]
        return ids == self.annotation_ids


@pytest.fixture
def batch_indexer(db_session, es_client, pyramid_request, moderation_service):
    return h.search.index.BatchIndexer(
        db_session, es_client, pyramid_request, es_client.index
    )


@pytest.fixture
def AnnotationTransformEvent(patch):
    return patch("h.search.index.AnnotationTransformEvent")


@pytest.fixture
def AnnotationSearchIndexPresenter(patch):
    class_ = patch("h.search.index.presenters.AnnotationSearchIndexPresenter")
    class_.return_value.asdict.return_value = {"test": "val"}
    return class_


@pytest.fixture
def search(es_client, request):
    return elasticsearch_dsl.Search(using=es_client.conn, index=es_client.index)


@pytest.fixture
def get_indexed_ann(es_client):
    def _get(annotation_id):
        """
        Return the annotation with the given ID from Elasticsearch.

        Raises if the annotation is not found.
        """
        return es_client.conn.get(
            index=es_client.index, doc_type=es_client.mapping_type, id=annotation_id
        )["_source"]

    return _get
