import logging
from unittest.mock import sentinel

import pytest
from elasticsearch.exceptions import NotFoundError

from h.search.index import BatchIndexer

pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


@pytest.mark.usefixtures("nipsa_service")
class TestBatchIndexer:
    @pytest.mark.parametrize("target_index", (None, "custom_index"))
    def test_it_accepts_different_indexes(self, target_index, es_client):
        indexer = BatchIndexer(
            session=sentinel.db,
            es_client=es_client,
            request=sentinel.request,
            target_index=target_index,
        )

        assert (
            indexer._target_index == target_index  # pylint:disable=protected-access
            if target_index
            else es_client.index
        )

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
            with pytest.raises(NotFoundError):
                get_indexed_ann(_id)

    def test_it_does_not_index_deleted_annotations(
        self, batch_indexer, factories, get_indexed_ann
    ):
        ann = factories.Annotation()
        # create deleted annotations
        ann_del = factories.Annotation(deleted=True)

        batch_indexer.index([ann.id, ann_del.id])

        assert get_indexed_ann(ann.id) is not None

        with pytest.raises(NotFoundError):
            get_indexed_ann(ann_del.id)

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
                assert "indexed 0k annotations, rate=" in record.getMessage()
        assert num_index_records == num_annotations // window_size

    def test_it_correctly_indexes_fields_for_bulk_actions(
        self, batch_indexer, factories, get_indexed_ann
    ):
        annotations = factories.Annotation.create_batch(2, groupid="group_a")

        batch_indexer.index([annotation.id for annotation in annotations])

        for ann in annotations:
            result = get_indexed_ann(ann.id)
            assert result.get("group") == ann.groupid
            assert result.get("authority") == ann.authority
            assert result.get("user") == ann.userid
            assert result.get("uri") == ann.target_uri

    def test_it_returns_errored_annotation_ids(
        self, batch_indexer, factories, es_helpers
    ):
        annotations = factories.Annotation.create_batch(3)
        expected_errored_ids = {annotations[0].id, annotations[2].id}

        es_helpers.streaming_bulk.return_value = [
            (False, {"index": {"error": "some error", "_id": annotations[0].id}}),
            (True, {}),
            (False, {"index": {"error": "some error", "_id": annotations[2].id}}),
        ]

        errored = batch_indexer.index([annotation.id for annotation in annotations])

        assert errored == expected_errored_ids

    def test_it_does_not_error_if_annotations_already_indexed(
        self, db_session, es_client, factories, pyramid_request, es_helpers
    ):
        annotations = factories.Annotation.create_batch(3)
        expected_errored_ids = {annotations[1].id}

        es_helpers.streaming_bulk.return_value = [
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

        errored = BatchIndexer(
            db_session, es_client, pyramid_request, es_client.index, "create"
        ).index([annotation.id for annotation in annotations])

        assert errored == expected_errored_ids

    def test_delete(self, batch_indexer, factories, get_indexed_ann):
        annotations = factories.Annotation.create_batch(2)
        batch_indexer.index([annotation.id for annotation in annotations])

        batch_indexer.delete([annotation.id for annotation in annotations])

        for annotation in annotations:
            assert get_indexed_ann(annotation.id) == {"doc": {"deleted": True}}


@pytest.fixture
def batch_indexer(  # pylint:disable=unused-argument
    db_session, es_client, pyramid_request, moderation_service
):
    return BatchIndexer(db_session, es_client, pyramid_request)


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


@pytest.fixture
def es_helpers(patch):
    return patch("h.search.index.es_helpers")
