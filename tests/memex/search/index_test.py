# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest

import elasticsearch

from memex import presenters
from memex.search import client
from memex.search import index


@pytest.mark.usefixtures('presenters')
class TestIndexAnnotation:

    def test_it_presents_the_annotation(self, es, presenters, pyramid_request):
        annotation = mock.Mock()

        index.index(es, annotation, pyramid_request)

        presenters.AnnotationSearchIndexPresenter.assert_called_once_with(annotation)

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
        presenters = patch('memex.search.index.presenters')
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
        return patch('memex.search.index.log')


@pytest.mark.usefixtures('BatchDeleter',
                         'BatchIndexer',
                         'configure_index',
                         'get_aliased_index',
                         'update_aliased_index')
class TestReindex(object):
    def test_indexes_annotations(self, es, indexer):
        """Should call .index() on the batch indexer instance."""
        index.reindex(mock.sentinel.session, es, mock.sentinel.request)

        indexer.index.assert_called_once_with()

    def test_retries_failed_annotations(self, es, indexer):
        """Should call .index() a second time with any failed annotation IDs."""
        indexer.index.return_value = ['abc123', 'def456']

        index.reindex(mock.sentinel.session, es, mock.sentinel.request)

        assert indexer.index.mock_calls == [
            mock.call(),
            mock.call(['abc123', 'def456']),
        ]

    def test_creates_new_index_if_aliased(self, es, configure_index, matchers):
        """If the current index isn't concrete, then create a new target index."""
        index.reindex(mock.sentinel.session, es, mock.sentinel.request)

        configure_index.assert_called_once_with(es, matchers.regex('hypothesis-[0-9a-f]{8}'))

    def test_passes_new_index_to_indexer_if_aliased(self, es, matchers, BatchIndexer):
        """Pass the name of any new index as target_index to indexer."""
        index.reindex(mock.sentinel.session, es, mock.sentinel.request)

        _, kwargs = BatchIndexer.call_args
        assert kwargs['target_index'] == matchers.regex('hypothesis-[0-9a-f]{8}')

    def test_updates_alias_when_reindexed_if_aliased(self, es, matchers, update_aliased_index):
        """Call update_aliased_index on the client with the new index name."""
        index.reindex(mock.sentinel.session, es, mock.sentinel.request)

        update_aliased_index.assert_called_once_with(es, matchers.regex('hypothesis-[0-9a-f]{8}'))

    def test_does_not_update_alias_if_indexing_fails(self, es, indexer, update_aliased_index):
        """Don't call update_aliased_index if index() fails..."""
        indexer.index.side_effect = RuntimeError('fail')

        try:
            index.reindex(mock.sentinel.session, es, mock.sentinel.request)
        except RuntimeError:
            pass

        assert not update_aliased_index.called

    def test_runs_deleter_if_not_aliased(self, es, deleter, get_aliased_index):
        """If dealing with a concrete index, run the deleter."""
        get_aliased_index.return_value = None

        index.reindex(mock.sentinel.session, es, mock.sentinel.request)

        deleter.delete_all.assert_called_once_with()

    def test_does_not_run_deleter_if_aliased(self, es, deleter):
        """If dealing with an alias, do not run the deleter."""
        index.reindex(mock.sentinel.session, es, mock.sentinel.request)

        deleter.delete_all.assert_not_called()

    @pytest.fixture
    def BatchDeleter(self, patch):
        return patch('memex.search.index.BatchDeleter')

    @pytest.fixture
    def BatchIndexer(self, patch):
        return patch('memex.search.index.BatchIndexer')

    @pytest.fixture
    def configure_index(self, patch):
        return patch('memex.search.index.configure_index')

    @pytest.fixture
    def get_aliased_index(self, patch):
        func = patch('memex.search.index.get_aliased_index')
        func.return_value = 'foobar'
        return func

    @pytest.fixture
    def update_aliased_index(self, patch):
        return patch('memex.search.index.update_aliased_index')

    @pytest.fixture
    def deleter(self, BatchDeleter):
        return BatchDeleter.return_value

    @pytest.fixture
    def indexer(self, BatchIndexer):
        indexer = BatchIndexer.return_value
        indexer.index.return_value = []
        return indexer


class TestBatchIndexer(object):
    def test_index_indexes_all_annotations_to_es(self, db_session, indexer, matchers, streaming_bulk, factories):
        ann_1, ann_2 = factories.Annotation(), factories.Annotation()

        indexer.index()

        streaming_bulk.assert_called_once_with(
            indexer.es_client.conn, matchers.iterable_with([ann_1, ann_2]),
            chunk_size=mock.ANY, raise_on_error=False, expand_action_callback=mock.ANY)

    def test_index_indexes_filtered_annotations_to_es(self, db_session, indexer, matchers, streaming_bulk, factories):
        ann_1, ann_2 = factories.Annotation(), factories.Annotation()

        indexer.index([ann_2.id])

        streaming_bulk.assert_called_once_with(
            indexer.es_client.conn, matchers.iterable_with([ann_2]),
            chunk_size=mock.ANY, raise_on_error=False, expand_action_callback=mock.ANY)

    def test_index_correctly_presents_bulk_actions(self,
                                                   db_session,
                                                   indexer,
                                                   pyramid_request,
                                                   streaming_bulk,
                                                   factories):
        annotation = factories.Annotation()
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

        rendered = presenters.AnnotationSearchIndexPresenter(annotation).asdict()
        rendered['target'][0]['scope'] = [annotation.target_uri_normalized]
        assert results[0] == (
            {'index': {'_type': indexer.es_client.t.annotation,
                       '_index': 'hypothesis',
                       '_id': annotation.id}},
            rendered
        )

    def test_index_emits_AnnotationTransformEvent_when_presenting_bulk_actions(self,
                                                                               db_session,
                                                                               indexer,
                                                                               pyramid_request,
                                                                               streaming_bulk,
                                                                               pyramid_config,
                                                                               factories):

        annotation = factories.Annotation()
        results = []

        def fake_streaming_bulk(*args, **kwargs):
            ann = list(args[1])[0]
            callback = kwargs.get('expand_action_callback')
            results.append(callback(ann))
            return set()

        streaming_bulk.side_effect = fake_streaming_bulk

        def transform(event):
            data = event.annotation_dict
            data['transformed'] = True

        pyramid_config.add_subscriber(transform, 'memex.events.AnnotationTransformEvent')

        indexer.index()

        rendered = presenters.AnnotationSearchIndexPresenter(annotation).asdict()
        rendered['transformed'] = True
        rendered['target'][0]['scope'] = [annotation.target_uri_normalized]

        assert results[0] == (
            {'index': {'_type': indexer.es_client.t.annotation,
                       '_index': 'hypothesis',
                       '_id': annotation.id}},
            rendered
        )

    def test_index_returns_failed_bulk_actions(self, db_session, indexer, streaming_bulk, factories):
        ann_success_1, ann_success_2 = factories.Annotation(), factories.Annotation()
        ann_fail_1, ann_fail_2 = factories.Annotation(), factories.Annotation()

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
    def indexer(self, db_session, es, pyramid_request):
        return index.BatchIndexer(db_session, es, pyramid_request)

    @pytest.fixture
    def index(self, patch):
        return patch('memex.search.index.BatchIndexer.index')

    @pytest.fixture
    def streaming_bulk(self, patch):
        return patch('memex.search.index.es_helpers.streaming_bulk')


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
             '_source': presenters.AnnotationSearchIndexPresenter(annotation)}]

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
        return patch('memex.search.index.BatchDeleter.deleted_annotation_ids')

    @pytest.fixture
    def delete(self, patch):
        return patch('memex.search.index.BatchDeleter.delete')

    @pytest.fixture
    def es_scan(self, patch):
        return patch('memex.search.index.es_helpers.scan')

    @pytest.fixture
    def streaming_bulk(self, patch):
        return patch('memex.search.index.es_helpers.streaming_bulk')

    @pytest.fixture
    def annotation(self, db_session, factories):
        ann = factories.Annotation(userid="bob", target_uri="http://example.com")
        return ann


@pytest.fixture
def es():
    mock_es = mock.Mock(spec=client.Client('localhost', 'hypothesis'))
    mock_es.index = 'hypothesis'
    mock_es.t.annotation = 'annotation'
    mock_es.get_aliased_index.return_value = None
    return mock_es


@pytest.fixture
def AnnotationTransformEvent(patch):
    return patch('memex.search.index.AnnotationTransformEvent')
