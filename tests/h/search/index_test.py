# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest

from h import presenters
from h.search import index
from h.search import query
from h.search import client


@pytest.mark.usefixtures('presenters')
class TestIndexAnnotation:
    """
    Annotation indexing tests that use a mock ElasticSearch connection.
    """

    def test_it_presents_the_annotation(self, es, presenters, pyramid_request):
        annotation = mock.Mock()

        index.index(es, annotation, pyramid_request)

        presenters.AnnotationSearchIndexPresenter.assert_called_once_with(annotation)

    def test_it_creates_an_annotation_before_save_event(self,
                                                        AnnotationTransformEvent,
                                                        es,
                                                        presenters,
                                                        pyramid_request):
        annotation = mock.Mock()
        presented = presenters.AnnotationSearchIndexPresenter.return_value.asdict()

        index.index(es, annotation, pyramid_request)

        AnnotationTransformEvent.assert_called_once_with(pyramid_request, annotation, presented)

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
            refresh=False,
        )

    def test_it_allows_to_override_target_index(self, es, presenters, pyramid_request):
        index.index(es, mock.Mock(), pyramid_request, target_index='custom-index')

        _, kwargs = es.conn.index.call_args
        assert kwargs['index'] == 'custom-index'

    @pytest.fixture
    def presenters(self, patch):
        presenters = patch('h.search.index.presenters')
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


class TestIndexAnnotationWithES:
    """
    Annotation search tests that use a real ElasticSearch connection.
    """

    def test_indexes_top_level(self, factories, pyramid_request, search_client):
        index.index(search_client, factories.Annotation(), pyramid_request, refresh=True)
        index.index(search_client, factories.Annotation(references=['OHFscuRvTmiwpOHWfrbzxw']), pyramid_request, refresh=True)

        builder = query.Builder()
        builder.append_filter(query.TopLevelAnnotationsFilter())
        assert count_hits(search_client, builder.build({})) == 1

    def test_indexes_authority(self, factories, pyramid_request, search_client):
        index.index(search_client, factories.Annotation(userid='acct:jim@partner.org'), pyramid_request, refresh=True)
        index.index(search_client, factories.Annotation(userid='acct:jim@decoy.org'), pyramid_request, refresh=True)

        builder = query.Builder()
        builder.append_filter(query.AuthorityFilter('partner.org'))
        assert count_hits(search_client, builder.build({})) == 1

    def test_indexes_auth(self, factories, pyramid_request, search_client):
        index.index(search_client, factories.Annotation(userid='acct:jim@partner.org'), pyramid_request, refresh=True)
        index.index(search_client, factories.Annotation(userid='acct:jim@partner.org', shared=True), pyramid_request, refresh=True)

        builder = query.Builder()
        builder.append_filter(query.AuthFilter(mock.Mock(authenticated_userid=None)))
        assert count_hits(search_client, builder.build({})) == 1

        builder = query.Builder()
        builder.append_filter(query.AuthFilter(mock.Mock(authenticated_userid='acct:jim@partner.org')))
        assert count_hits(search_client, builder.build({})) == 2

    def test_indexes_group(self, factories, pyramid_request, search_client):
        index.index(search_client, factories.Annotation(groupid='foo'), pyramid_request, refresh=True)
        index.index(search_client, factories.Annotation(groupid='bar'), pyramid_request, refresh=True)

        builder = query.Builder()
        builder.append_filter(query.GroupFilter())
        assert count_hits(search_client, builder.build({'group': 'foo'})) == 1

    def test_indexes_deleted(self, factories, pyramid_request, search_client):
        ann = factories.Annotation()
        index.index(search_client, ann, pyramid_request, refresh=True)
        index.delete(search_client, ann.id, refresh=True)

        index.index(search_client, factories.Annotation(), pyramid_request, refresh=True)

        builder = query.Builder()
        builder.append_filter(query.DeletedFilter())
        assert count_hits(search_client, builder.build({})) == 1


class TestDeleteAnnotation:

    def test_it_marks_annotation_as_deleted(self, es):
        index.delete(es, 'test_annotation_id')

        es.conn.index.assert_called_once_with(
            index='hypothesis',
            doc_type='annotation',
            body={'deleted': True},
            id='test_annotation_id',
            refresh=False,
        )

    def test_it_allows_to_override_target_index(self, es):
        index.delete(es, 'test_annotation_id', target_index='custom-index')

        _, kwargs = es.conn.index.call_args
        assert kwargs['index'] == 'custom-index'


class TestBatchIndexer(object):
    def test_index_indexes_all_annotations_to_es(self, db_session, indexer, matchers, streaming_bulk, factories):
        ann_1, ann_2 = factories.Annotation(), factories.Annotation()

        indexer.index()

        streaming_bulk.assert_called_once_with(
            indexer.es_client.conn, matchers.iterable_with(matchers.unordered_list([ann_1, ann_2])),
            chunk_size=mock.ANY, raise_on_error=False, expand_action_callback=mock.ANY)

    def test_index_skips_deleted_annotations_when_indexing_all(self, db_session, indexer, matchers, streaming_bulk, factories):
        ann_1, ann_2 = factories.Annotation(), factories.Annotation()
        # create deleted annotations
        factories.Annotation(deleted=True)
        factories.Annotation(deleted=True)

        indexer.index()

        streaming_bulk.assert_called_once_with(
            indexer.es_client.conn, matchers.iterable_with(matchers.unordered_list([ann_1, ann_2])),
            chunk_size=mock.ANY, raise_on_error=False, expand_action_callback=mock.ANY)

    def test_index_indexes_filtered_annotations_to_es(self, db_session, indexer, matchers, streaming_bulk, factories):
        _, ann_2 = factories.Annotation(), factories.Annotation()  # noqa: F841

        indexer.index([ann_2.id])

        streaming_bulk.assert_called_once_with(
            indexer.es_client.conn, matchers.iterable_with([ann_2]),
            chunk_size=mock.ANY, raise_on_error=False, expand_action_callback=mock.ANY)

    def test_index_skips_deleted_annotations_when_indexing_filtered(self, db_session, indexer, matchers, streaming_bulk, factories):
        factories.Annotation()
        ann_2 = factories.Annotation()
        # create deleted annotations
        factories.Annotation(deleted=True)
        factories.Annotation(deleted=True)

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
            if event.annotation == annotation:
                data = event.annotation_dict
                data['transformed'] = True

        pyramid_config.add_subscriber(transform, 'h.events.AnnotationTransformEvent')

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

    def test_index_returns_failed_bulk_actions_for_default_op_type(self, db_session, indexer, streaming_bulk, factories):
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

    def test_index_returns_failed_bulk_actions_for_create_op_type(self, pyramid_request, es, db_session, streaming_bulk, factories):
        indexer = index.BatchIndexer(db_session, es, pyramid_request,
                                     op_type='create')

        ann_success_1, ann_success_2 = factories.Annotation(), factories.Annotation()
        ann_fail_1, ann_fail_2 = factories.Annotation(), factories.Annotation()

        def fake_streaming_bulk(*args, **kwargs):
            for ann in args[1]:
                if ann.id in [ann_fail_1.id, ann_fail_2.id]:
                    yield (False, {'create': {'_id': ann.id, 'error': 'unknown error'}})
                elif ann.id in [ann_success_1.id, ann_success_2.id]:
                    yield (True, {'create': {'_id': ann.id}})

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
                            'document already exists]'
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
        return patch('h.search.index.BatchIndexer.index')

    @pytest.fixture
    def streaming_bulk(self, patch):
        return patch('h.search.index.es_helpers.streaming_bulk')


def count_hits(search_client, body):
    result = search_client.conn.search(body=body,
                                       index=search_client.index)
    return result['hits']['total']


@pytest.fixture
def es():
    mock_es = mock.Mock(spec=client.Client('localhost', 'hypothesis'))
    mock_es.index = 'hypothesis'
    mock_es.t.annotation = 'annotation'
    return mock_es


@pytest.fixture
def AnnotationTransformEvent(patch):
    return patch('h.search.index.AnnotationTransformEvent')
