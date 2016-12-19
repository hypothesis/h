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


class TestDeleteAnnotation:

    def test_it_marks_annotation_as_deleted(self, es):
        index.delete(es, 'test_annotation_id')

        es.conn.index.assert_called_once_with(
            index='hypothesis',
            doc_type='annotation',
            body={'deleted': True},
            id='test_annotation_id'
        )


@pytest.mark.usefixtures('BatchIndexer',
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

    def test_creates_new_index(self, es, configure_index, matchers):
        """Creates a new target index."""
        index.reindex(mock.sentinel.session, es, mock.sentinel.request)

        configure_index.assert_called_once_with(es)

    def test_passes_new_index_to_indexer(self, es, configure_index, BatchIndexer):
        """Pass the name of the new index as target_index to indexer."""
        configure_index.return_value = 'hypothesis-abcd1234'

        index.reindex(mock.sentinel.session, es, mock.sentinel.request)

        _, kwargs = BatchIndexer.call_args
        assert kwargs['target_index'] == 'hypothesis-abcd1234'

    def test_updates_alias_when_reindexed(self, es, configure_index, update_aliased_index):
        """Call update_aliased_index on the client with the new index name."""
        configure_index.return_value = 'hypothesis-abcd1234'

        index.reindex(mock.sentinel.session, es, mock.sentinel.request)

        update_aliased_index.assert_called_once_with(es, 'hypothesis-abcd1234')

    def test_does_not_update_alias_if_indexing_fails(self, es, indexer, update_aliased_index):
        """Don't call update_aliased_index if index() fails..."""
        indexer.index.side_effect = RuntimeError('fail')

        try:
            index.reindex(mock.sentinel.session, es, mock.sentinel.request)
        except RuntimeError:
            pass

        assert not update_aliased_index.called

    def test_raises_if_index_not_aliased(self, es, get_aliased_index):
        get_aliased_index.return_value = None

        with pytest.raises(RuntimeError):
            index.reindex(mock.sentinel.session, es, mock.sentinel.request)

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

    def test_index_allows_to_set_op_type(self, db_session, es, pyramid_request, streaming_bulk, factories):
        indexer = index.BatchIndexer(db_session, es, pyramid_request,
                                     op_type='create')
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
            {'create': {'_type': indexer.es_client.t.annotation,
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
                    yield (False, {'index': {'_id': ann.id, 'error': 'unknown error'}})
                elif ann.id in [ann_success_1.id, ann_success_2.id]:
                    yield (True, {'index': {'_id': ann.id}})

        streaming_bulk.side_effect = fake_streaming_bulk

        result = indexer.index()
        assert result == set([ann_fail_1.id, ann_fail_2.id])

    def test_index_ignores_document_exists_errors_for_op_type_create(self, db_session, es, pyramid_request, streaming_bulk, factories):
        indexer = index.BatchIndexer(db_session, es, pyramid_request,
                                     op_type='create')

        ann_success_1, ann_success_2 = factories.Annotation(), factories.Annotation()
        ann_fail_1, ann_fail_2 = factories.Annotation(), factories.Annotation()

        def fake_streaming_bulk(*args, **kwargs):
            for ann in args[1]:
                if ann.id in [ann_fail_1.id, ann_fail_2.id]:
                    error = 'DocumentAlreadyExistsException[[index-name][1] [annotation][gibberish]: ' \
                            'document already exist]'
                    yield (False, {'create': {'_id': ann.id, 'error': error}})
                elif ann.id in [ann_success_1.id, ann_success_2.id]:
                    yield (True, {'create': {'_id': ann.id}})

        streaming_bulk.side_effect = fake_streaming_bulk

        result = indexer.index()
        assert len(result) == 0

    @pytest.fixture
    def indexer(self, db_session, es, pyramid_request):
        return index.BatchIndexer(db_session, es, pyramid_request)

    @pytest.fixture
    def index(self, patch):
        return patch('memex.search.index.BatchIndexer.index')

    @pytest.fixture
    def streaming_bulk(self, patch):
        return patch('memex.search.index.es_helpers.streaming_bulk')


@pytest.fixture
def es():
    mock_es = mock.Mock(spec=client.Client('localhost', 'hypothesis'))
    mock_es.index = 'hypothesis'
    mock_es.t.annotation = 'annotation'
    return mock_es


@pytest.fixture
def AnnotationTransformEvent(patch):
    return patch('memex.search.index.AnnotationTransformEvent')
