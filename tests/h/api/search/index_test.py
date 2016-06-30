# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest

import elasticsearch

from h.api import models
from h.api import presenters
from h.api.search import client
from h.api.search import index


@pytest.mark.usefixtures('presenters')
class TestIndexAnnotation:

    def test_it_presents_the_annotation(self, es, presenters, pyramid_request):
        annotation = mock.Mock()

        index.index(es, annotation, pyramid_request)

        presenters.AnnotationSearchIndexPresenter.assert_called_once_with(
            pyramid_request,
            annotation)

    def test_it_creates_an_annotation_before_save_event(self,
                                                        AnnotationTransformEvent,
                                                        es,
                                                        presenters,
                                                        pyramid_request):
        presented = presenters.AnnotationSearchIndexPresenter.return_value.asdict()

        index.index(es, mock.Mock(), pyramid_request)

        AnnotationTransformEvent.assert_called_once_with(pyramid_request, presented)

    def test_it_notifies_before_save_event(self,
                                           AnnotationTransformEvent,
                                           es,
                                           notify,
                                           presenters,
                                           pyramid_request):
        index.index(es, mock.Mock(), pyramid_request)

        event = AnnotationTransformEvent.return_value
        notify.assert_called_once_with(event)

    def test_it_indexes_the_annotation(self, es, presenters, pyramid_request):
        index.index(es, mock.Mock(), pyramid_request)

        es.conn.index.assert_called_once_with(
            index='hypothesis',
            doc_type='annotation',
            body=presenters.AnnotationSearchIndexPresenter.return_value.asdict.return_value,
            id='test_annotation_id',
        )

    @pytest.fixture
    def presenters(self, patch):
        presenters = patch('h.api.search.index.presenters')
        presenter = presenters.AnnotationSearchIndexPresenter.return_value
        presenter.asdict.return_value = {
            'id': 'test_annotation_id',
            'target': [
                {
                    'source': 'http://example.com/example',
                },
            ],
        }
        return presenters

    @pytest.fixture
    def AnnotationTransformEvent(self, patch):
        return patch('h.api.search.index.AnnotationTransformEvent')


@pytest.mark.usefixtures('log')
class TestDeleteAnnotation:

    def test_it_deletes_the_annotation(self, es):
        index.delete(es, 'test_annotation_id')

        es.conn.delete.assert_called_once_with(
            index='hypothesis',
            doc_type='annotation',
            id='test_annotation_id',
        )

    def test_it_logs_NotFoundErrors(self, es, log):
        """NotFoundErrors from elasticsearch should be caught and logged."""
        es.conn.delete.side_effect = elasticsearch.NotFoundError()

        index.delete(es, mock.Mock())

        assert log.exception.called

    @pytest.fixture
    def log(self, patch):
        return patch('h.api.search.index.log')


@pytest.mark.usefixtures('BatchIndexer', 'BatchDeleter')
class TestReindex(object):
    def test_it_indexes_all_annotations(self, BatchIndexer):
        index.reindex(mock.sentinel.session, mock.sentinel.es, mock.sentinel.request)

        BatchIndexer.assert_called_once_with(
            mock.sentinel.session, mock.sentinel.es, mock.sentinel.request)
        assert BatchIndexer.return_value.index_all.called

    def test_it_removes_all_deleted_annotations(self, BatchDeleter):
        index.reindex(mock.sentinel.session, mock.sentinel.es, mock.sentinel.request)

        BatchDeleter.assert_called_once_with(mock.sentinel.session, mock.sentinel.es)
        assert BatchDeleter.return_value.delete_all.called

    @pytest.fixture
    def BatchIndexer(self, patch):
        return patch('h.api.search.index.BatchIndexer')

    @pytest.fixture
    def BatchDeleter(self, patch):
        return patch('h.api.search.index.BatchDeleter')


class TestBatchIndexer(object):
    def test_index_all(self, indexer, index):
        indexer.index_all()
        assert index.called

    def test_index_all_retries_failed_index_attempts_once(self, indexer, index):
        index.return_value = set(['id-1'])
        indexer.index_all()
        assert index.call_args_list == [
            mock.call(indexer, None),
            mock.call(indexer, set(['id-1'])),
        ]

    def test_index_indexes_all_annotations_to_es(self, db_session, indexer, matchers, streaming_bulk):
        ann_1, ann_2 = self.annotation(), self.annotation()
        db_session.add_all([ann_1, ann_2])
        db_session.flush()

        indexer.index()

        streaming_bulk.assert_called_once_with(
            indexer.es_client.conn, matchers.iterable_with([ann_1, ann_2]),
            chunk_size=mock.ANY, raise_on_error=False, expand_action_callback=mock.ANY)

    def test_index_indexes_filtered_annotations_to_es(self, db_session, indexer, matchers, streaming_bulk):
        ann_1, ann_2 = self.annotation(), self.annotation()
        db_session.add_all([ann_1, ann_2])
        db_session.flush()

        indexer.index([ann_2.id])

        streaming_bulk.assert_called_once_with(
            indexer.es_client.conn, matchers.iterable_with([ann_2]),
            chunk_size=mock.ANY, raise_on_error=False, expand_action_callback=mock.ANY)

    def test_index_correctly_presents_bulk_actions(self,
                                                   db_session,
                                                   indexer,
                                                   pyramid_request,
                                                   streaming_bulk):
        annotation = self.annotation()
        db_session.add(annotation)
        db_session.flush()
        results = []

        def fake_streaming_bulk(*args, **kwargs):
            ann = list(args[1])[0]
            callback = kwargs.get('expand_action_callback')
            results.append(callback(ann))
            return set()

        streaming_bulk.side_effect = fake_streaming_bulk

        indexer.index()

        rendered = presenters.AnnotationSearchIndexPresenter(
            pyramid_request, annotation).asdict()
        rendered['target'][0]['scope'] = [annotation.target_uri_normalized]
        assert results[0] == (
            {'index': {'_type': indexer.es_client.t.annotation,
                       '_index': indexer.es_client.index,
                       '_id': annotation.id}},
            rendered
        )

    def test_index_returns_failed_bulk_actions(self, db_session, indexer, streaming_bulk):
        ann_success_1, ann_success_2 = self.annotation(), self.annotation()
        ann_fail_1, ann_fail_2 = self.annotation(), self.annotation()
        db_session.add_all([ann_success_1, ann_success_2,
                            ann_fail_1, ann_fail_2])
        db_session.flush()

        def fake_streaming_bulk(*args, **kwargs):
            for ann in args[1]:
                if ann.id in [ann_fail_1.id, ann_fail_2.id]:
                    yield (False, {'index': {'_id': ann.id}})
                elif ann.id in [ann_success_1.id, ann_success_2.id]:
                    yield (True, {'index': {'_id': ann.id}})

        streaming_bulk.side_effect = fake_streaming_bulk

        result = indexer.index()
        assert result == set([ann_fail_1.id, ann_fail_2.id])

    @pytest.fixture
    def indexer(self, db_session, pyramid_request):
        return index.BatchIndexer(db_session, mock.MagicMock(), pyramid_request)

    @pytest.fixture
    def index(self, patch):
        return patch('h.api.search.index.BatchIndexer.index')

    @pytest.fixture
    def streaming_bulk(self, patch):
        return patch('h.api.search.index.es_helpers.streaming_bulk')

    def annotation(self):
        return models.Annotation(userid="bob", target_uri="http://example.com")


class TestBatchDeleter(object):
    def test_delete_all_fetches_deleted_annotation_ids(self, deleter, deleted_annotation_ids):
        deleter.delete_all()
        assert deleted_annotation_ids.call_count == 1

    def test_delete_all_deletes_annotation_ids(self, deleter, deleted_annotation_ids, delete):
        deleted_annotation_ids.return_value = set([mock.Mock()])
        delete.return_value = set()

        deleter.delete_all()
        delete.assert_called_once_with(deleter, deleted_annotation_ids.return_value)

    def test_delete_all_skips_deleting_when_no_deleted_annotation_ids(self,
                                                                      deleter,
                                                                      deleted_annotation_ids,
                                                                      delete):
        deleted_annotation_ids.return_value = set()

        deleter.delete_all()
        assert not delete.called

    def test_delete_all_retries_failed_deletion_attempts_once(self,
                                                              deleter,
                                                              deleted_annotation_ids,
                                                              delete):
        deleted_annotation_ids.return_value = set(['id-1', 'id-2'])
        delete.return_value = set(['id-1'])

        deleter.delete_all()
        assert delete.call_args_list == [
            mock.call(deleter, set(['id-1', 'id-2'])),
            mock.call(deleter, set(['id-1']))
        ]

    def test_deleted_annotation_ids(self, db_session, es_scan, annotation):
        deleter = self.deleter(session=db_session)

        es_scan.return_value = [
            {'_id': 'deleted-from-postgres-id',
             '_source': {'uri': 'http://example.org'}}]

        deleted_ids = deleter.deleted_annotation_ids()
        assert deleted_ids == set(['deleted-from-postgres-id'])

    def test_deleted_annotation_ids_no_changes(self,
                                               annotation,
                                               db_session,
                                               es_scan,
                                               pyramid_request):
        deleter = self.deleter(session=db_session)

        es_scan.return_value = [
            {'_id': annotation.id,
             '_source': presenters.AnnotationSearchIndexPresenter(pyramid_request,
                                                                  annotation)}]

        deleted_ids = deleter.deleted_annotation_ids()
        assert len(deleted_ids) == 0

    def test_delete_deletes_from_es(self, deleter, streaming_bulk):
        ids = set(['test-annotation-id'])

        deleter.delete(ids)
        streaming_bulk.assert_called_once_with(
            deleter.es_client.conn, ids, chunk_size=mock.ANY,
            raise_on_error=False, expand_action_callback=mock.ANY)

    def test_delete_correctly_presents_bulk_actions(self, deleter, streaming_bulk):
        results = []

        def fake_streaming_bulk(*args, **kwargs):
            id_ = args[1][0]
            callback = kwargs.get('expand_action_callback')
            results.append(callback(id_))
            return set()

        streaming_bulk.side_effect = fake_streaming_bulk

        deleter.delete(['test-annotation-id'])
        assert results[0] == (
            {'delete': {'_type': deleter.es_client.t.annotation,
                        '_index': deleter.es_client.index,
                        '_id': 'test-annotation-id'}},
            None,
        )

    def test_delete_returns_failed_bulk_actions(self, deleter, streaming_bulk):
        def fake_streaming_bulk(*args, **kwargs):
            ids = args[1]
            for id_ in ids:
                if id_.startswith('fail'):
                    yield (False, {'delete': {'_id': id_, 'status': 504}})
                else:
                    yield (True, {'delete': {'_id': id_, 'status': 200}})

        streaming_bulk.side_effect = fake_streaming_bulk

        result = deleter.delete(['succeed-1', 'fail-1', 'fail-2', 'succeed-2'])
        assert result == set(['fail-1', 'fail-2'])

    def test_delete_does_not_return_failed_404_bulk_actions(self, deleter, streaming_bulk):
        def fake_streaming_bulk(*args, **kwargs):
            ids = args[1]
            for id_ in ids:
                if id_ == 'fail-404':
                    yield (False, {'delete': {'_id': id_, 'status': 404}})
                elif id_.startswith('fail-504'):
                    yield (False, {'delete': {'_id': id_, 'status': 504}})
                else:
                    yield (True, {'delete': {'_id': id_, 'status': 200}})

        streaming_bulk.side_effect = fake_streaming_bulk

        result = deleter.delete(['succeed-1', 'fail-404', 'fail-504'])
        assert result == set(['fail-504'])

    @pytest.fixture
    def deleter(self, session=None):
        if session is None:
            session = mock.MagicMock()
        return index.BatchDeleter(session, mock.MagicMock())

    @pytest.fixture
    def deleted_annotation_ids(self, patch):
        return patch('h.api.search.index.BatchDeleter.deleted_annotation_ids')

    @pytest.fixture
    def delete(self, patch):
        return patch('h.api.search.index.BatchDeleter.delete')

    @pytest.fixture
    def es_scan(self, patch):
        return patch('h.api.search.index.es_helpers.scan')

    @pytest.fixture
    def streaming_bulk(self, patch):
        return patch('h.api.search.index.es_helpers.streaming_bulk')

    @pytest.fixture
    def annotation(self, db_session):
        ann = models.Annotation(userid="bob", target_uri="http://example.com")
        db_session.add(ann)
        db_session.flush()
        return ann


@pytest.fixture
def es():
    mock_es = mock.Mock(spec=client.Client('localhost', 'hypothesis'))
    mock_es.index = 'hypothesis'
    mock_es.t.annotation = 'annotation'
    return mock_es
