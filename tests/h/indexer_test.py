# -*- coding: utf-8 -*-

import mock
import pytest

from memex import events
from memex.search import client
from h import indexer


@pytest.mark.usefixtures('BatchIndexer',
                         'configure_index',
                         'get_aliased_index',
                         'update_aliased_index')
class TestReindex(object):
    def test_sets_op_type_to_create(self, es, BatchIndexer):
        indexer.reindex(mock.sentinel.session, es, mock.sentinel.request)

        _, kwargs = BatchIndexer.call_args
        assert kwargs['op_type'] == 'create'

    def test_indexes_annotations(self, es, batchindexer):
        """Should call .index() on the batch indexer instance."""
        indexer.reindex(mock.sentinel.session, es, mock.sentinel.request)

        batchindexer.index.assert_called_once_with()

    def test_retries_failed_annotations(self, es, batchindexer):
        """Should call .index() a second time with any failed annotation IDs."""
        batchindexer.index.return_value = ['abc123', 'def456']

        indexer.reindex(mock.sentinel.session, es, mock.sentinel.request)

        assert batchindexer.index.mock_calls == [
            mock.call(),
            mock.call(['abc123', 'def456']),
        ]

    def test_creates_new_index(self, es, configure_index, matchers):
        """Creates a new target index."""
        indexer.reindex(mock.sentinel.session, es, mock.sentinel.request)

        configure_index.assert_called_once_with(es)

    def test_passes_new_index_to_indexer(self, es, configure_index, BatchIndexer):
        """Pass the name of the new index as target_index to indexer."""
        configure_index.return_value = 'hypothesis-abcd1234'

        indexer.reindex(mock.sentinel.session, es, mock.sentinel.request)

        _, kwargs = BatchIndexer.call_args
        assert kwargs['target_index'] == 'hypothesis-abcd1234'

    def test_updates_alias_when_reindexed(self, es, configure_index, update_aliased_index):
        """Call update_aliased_index on the client with the new index name."""
        configure_index.return_value = 'hypothesis-abcd1234'

        indexer.reindex(mock.sentinel.session, es, mock.sentinel.request)

        update_aliased_index.assert_called_once_with(es, 'hypothesis-abcd1234')

    def test_does_not_update_alias_if_indexing_fails(self, es, batchindexer, update_aliased_index):
        """Don't call update_aliased_index if index() fails..."""
        batchindexer.index.side_effect = RuntimeError('fail')

        try:
            indexer.reindex(mock.sentinel.session, es, mock.sentinel.request)
        except RuntimeError:
            pass

        assert not update_aliased_index.called

    def test_raises_if_index_not_aliased(self, es, get_aliased_index):
        get_aliased_index.return_value = None

        with pytest.raises(RuntimeError):
            indexer.reindex(mock.sentinel.session, es, mock.sentinel.request)

    @pytest.fixture
    def BatchIndexer(self, patch):
        return patch('h.indexer.BatchIndexer')

    @pytest.fixture
    def configure_index(self, patch):
        return patch('h.indexer.configure_index')

    @pytest.fixture
    def get_aliased_index(self, patch):
        func = patch('h.indexer.get_aliased_index')
        func.return_value = 'foobar'
        return func

    @pytest.fixture
    def update_aliased_index(self, patch):
        return patch('h.indexer.update_aliased_index')

    @pytest.fixture
    def batchindexer(self, BatchIndexer):
        indexer = BatchIndexer.return_value
        indexer.index.return_value = []
        return indexer

    @pytest.fixture
    def es(self):
        mock_es = mock.Mock(spec=client.Client('localhost', 'hypothesis'))
        mock_es.index = 'hypothesis'
        mock_es.t.annotation = 'annotation'
        return mock_es


@pytest.mark.usefixtures('add_annotation', 'delete_annotation')
class TestSubscribeAnnotationEvent(object):

    @pytest.mark.parametrize('action', ['create', 'update'])
    def test_it_enqueues_add_annotation_celery_task(self,
                                                    action,
                                                    add_annotation,
                                                    delete_annotation,
                                                    pyramid_request):
        event = events.AnnotationEvent(pyramid_request,
                                       {'id': 'test_annotation_id'},
                                       action)

        indexer.subscribe_annotation_event(event)

        add_annotation.delay.assert_called_once_with(event.annotation_id)
        assert not delete_annotation.delay.called

    def test_it_enqueues_delete_annotation_celery_task_for_delete(self,
                                                                  add_annotation,
                                                                  delete_annotation,
                                                                  pyramid_request):
        event = events.AnnotationEvent(pyramid_request,
                                       {'id': 'test_annotation_id'},
                                       'delete')

        indexer.subscribe_annotation_event(event)

        delete_annotation.delay.assert_called_once_with(event.annotation_id)
        assert not add_annotation.delay.called

    @pytest.fixture
    def add_annotation(self, patch):
        return patch('h.indexer.add_annotation')

    @pytest.fixture
    def delete_annotation(self, patch):
        return patch('h.indexer.delete_annotation')
