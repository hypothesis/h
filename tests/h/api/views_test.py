# -*- coding: utf-8 -*-

import mock
import pytest

from pyramid import testing

from h.api import models
from h.api import presenters
from h.api import views
from h.api.schemas import ValidationError


class TestError(object):

    def test_it_sets_status_code_from_error(self):
        request = testing.DummyRequest()
        exc = views.APIError("it exploded", status_code=429)

        views.error_api(exc, request)

        assert request.response.status_code == 429

    def test_it_returns_status_object(self):
        request = testing.DummyRequest()
        exc = views.APIError("it exploded", status_code=429)

        result = views.error_api(exc, request)

        assert result == {'status': 'failure', 'reason': 'it exploded'}

    def test_it_sets_bad_request_status_code(self):
        request = testing.DummyRequest()
        exc = mock.Mock(message="it exploded")

        views.error_validation(exc, request)

        assert request.response.status_code == 400


class TestIndex(object):

    def test_it_returns_the_right_links(self, config):
        config.add_route('api.search', '/dummy/search')
        config.add_route('api.annotations', '/dummy/annotations')
        config.add_route('api.annotation', '/dummy/annotations/:id')

        result = views.index(testing.DummyResource(), testing.DummyRequest())

        host = 'http://example.com'  # Pyramid's default host URL'
        links = result['links']
        assert links['annotation']['create']['method'] == 'POST'
        assert links['annotation']['create']['url'] == (
            host + '/dummy/annotations')
        assert links['annotation']['delete']['method'] == 'DELETE'
        assert links['annotation']['delete']['url'] == (
            host + '/dummy/annotations/:id')
        assert links['annotation']['read']['method'] == 'GET'
        assert links['annotation']['read']['url'] == (
            host + '/dummy/annotations/:id')
        assert links['annotation']['update']['method'] == 'PUT'
        assert links['annotation']['update']['url'] == (
            host + '/dummy/annotations/:id')
        assert links['search']['method'] == 'GET'
        assert links['search']['url'] == host + '/dummy/search'


@pytest.mark.usefixtures('search_lib')
class TestSearch(object):

    def test_it_searches(self, mock_request, search_lib):
        views.search(mock_request)

        search_lib.search.assert_called_once_with(mock_request,
                                                  mock_request.params,
                                                  separate_replies=False)

    def test_it_loads_annotations_from_database(self, mock_request, search_lib, storage):
        search_lib.search.return_value = {'total': 2,
                                          'rows': [{'id': 'row-1'}, {'id': 'row-2'}]}

        views.search(mock_request)

        storage.fetch_ordered_annotations.assert_called_once_with(
            mock_request.db, ['row-1', 'row-2'], load_documents=True)

    def test_it_renders_search_results(self, mock_request, search_lib):
        ann1 = models.Annotation(userid='luke')
        ann2 = models.Annotation(userid='sarah')
        mock_request.db.add_all([ann1, ann2])
        mock_request.db.flush()

        search_lib.search.return_value = {'total': 2,
                                          'rows': [{'id': ann1.id}, {'id': ann2.id}]}

        expected = {
            'total': 2,
            'rows': [
                presenters.AnnotationJSONPresenter(mock_request, ann1).asdict(),
                presenters.AnnotationJSONPresenter(mock_request, ann2).asdict(),
            ]
        }

        assert views.search(mock_request) == expected

    def test_it_loads_replies_from_database(self, mock_request, search_lib, storage):
        mock_request.params = {'_separate_replies': '1'}
        search_lib.search.return_value = {'total': 1,
                                          'rows': [{'id': 'row-1'}],
                                          'replies': [{'id': 'reply-1'},
                                                      {'id': 'reply-2'}]}

        views.search(mock_request)

        assert mock.call(mock_request.db, ['reply-1', 'reply-2'],
                         load_documents=True) in storage.fetch_ordered_annotations.call_args_list

    def test_it_renders_replies(self, mock_request, search_lib):
        ann = models.Annotation(userid='luke')
        mock_request.db.add(ann)
        mock_request.db.flush()
        reply1 = models.Annotation(userid='sarah', references=[ann.id])
        reply2 = models.Annotation(userid='sarah', references=[ann.id])
        mock_request.db.add_all([reply1, reply2])
        mock_request.db.flush()

        search_lib.search.return_value = {'total': 1,
                                          'rows': [{'id': ann.id}],
                                          'replies': [{'id': reply1.id}, {'id': reply2.id}],
                                          }

        mock_request.params = {'_separate_replies': '1'}

        expected = {
            'total': 1,
            'rows': [presenters.AnnotationJSONPresenter(mock_request, ann).asdict()],
            'replies': [
                presenters.AnnotationJSONPresenter(mock_request, reply1).asdict(),
                presenters.AnnotationJSONPresenter(mock_request, reply2).asdict(),
            ]
        }

        assert views.search(mock_request) == expected

    @pytest.fixture
    def search_lib(self, patch):
        return patch('h.api.views.search_lib')

    @pytest.fixture
    def storage(self, patch):
        return patch('h.api.views.storage')

    @pytest.fixture
    def mock_request(self, db_session):
        return testing.DummyRequest(db=db_session)


@pytest.mark.usefixtures('AnnotationEvent',
                         'AnnotationJSONPresenter',
                         'schemas',
                         'storage')
class TestCreate(object):

    def test_it_raises_if_json_parsing_fails(self, mock_request):
        """It raises PayloadError if parsing of the request body fails."""
        # Make accessing the request.json_body property raise ValueError.
        type(mock_request).json_body = mock.PropertyMock(
            side_effect=ValueError)

        with pytest.raises(views.PayloadError):
            views.create(mock_request)

    def test_it_inits_CreateAnnotationSchema(self, mock_request, schemas):
        views.create(mock_request)

        schemas.CreateAnnotationSchema.assert_called_once_with(mock_request)

    def test_it_validates_the_posted_data(self, mock_request, schemas):
        """It should call validate() with a request.json_body."""
        views.create(mock_request)

        schemas.CreateAnnotationSchema.return_value.validate\
            .assert_called_once_with(mock_request.json_body)

    def test_it_raises_if_validate_raises(self, mock_request, schemas):
        schemas.CreateAnnotationSchema.return_value.validate.side_effect = (
            ValidationError('asplode'))

        with pytest.raises(ValidationError) as exc:
            views.create(mock_request)

        assert exc.value.message == 'asplode'

    def test_it_creates_the_annotation_in_storage(self,
                                                  mock_request,
                                                  storage,
                                                  schemas):
        schema = schemas.CreateAnnotationSchema.return_value

        views.create(mock_request)

        storage.create_annotation.assert_called_once_with(
            mock_request, schema.validate.return_value)

    def test_it_raises_if_create_annotation_raises(self,
                                                   mock_request,
                                                   storage):
        storage.create_annotation.side_effect = ValidationError('asplode')

        with pytest.raises(ValidationError) as exc:
            views.create(mock_request)

        assert exc.value.message == 'asplode'

    def test_it_inits_AnnotationJSONPresenter(self,
                                              AnnotationJSONPresenter,
                                              mock_request,
                                              storage):
        views.create(mock_request)

        AnnotationJSONPresenter.assert_called_once_with(
            mock_request, storage.create_annotation.return_value)

    def test_it_publishes_annotation_event(self,
                                           AnnotationEvent,
                                           mock_request,
                                           storage):
        """It publishes an annotation "create" event for the annotation."""
        views.create(mock_request)

        annotation = storage.create_annotation.return_value

        AnnotationEvent.assert_called_once_with(
            mock_request, annotation.id, 'create', annotation_dict=None)
        mock_request.notify_after_commit.assert_called_once_with(
            AnnotationEvent.return_value)

    def test_it_returns_presented_annotation(self,
                                             AnnotationJSONPresenter,
                                             mock_request):
        result = views.create(mock_request)

        AnnotationJSONPresenter.return_value.asdict.assert_called_once_with()
        assert result == (
            AnnotationJSONPresenter.return_value.asdict.return_value)

    @pytest.fixture
    def mock_request(self):
        request = testing.DummyRequest(notify_after_commit=mock.Mock())
        type(request).json_body = mock.PropertyMock(return_value={})
        return request


@pytest.mark.usefixtures('AnnotationJSONPresenter')
class TestRead(object):

    def test_it_returns_presented_annotation(self, AnnotationJSONPresenter):
        annotation = mock.Mock()
        request = mock.Mock()
        presenter = mock.Mock()
        AnnotationJSONPresenter.return_value = presenter

        result = views.read(annotation, request)

        AnnotationJSONPresenter.assert_called_once_with(request, annotation)
        assert result == presenter.asdict()


@pytest.mark.usefixtures('AnnotationJSONLDPresenter')
class TestReadJSONLD(object):

    def test_it_sets_correct_content_type(self, AnnotationJSONLDPresenter):
        AnnotationJSONLDPresenter.CONTEXT_URL = 'http://foo.com/context.jsonld'

        annotation = mock.Mock()
        request = testing.DummyRequest()

        views.read_jsonld(annotation, request)

        assert request.response.content_type == 'application/ld+json'
        assert request.response.content_type_params == {
            'profile': 'http://foo.com/context.jsonld'
        }

    def test_it_returns_presented_annotation(self, AnnotationJSONLDPresenter):
        annotation = mock.Mock()
        presenter = mock.Mock()
        AnnotationJSONLDPresenter.return_value = presenter
        AnnotationJSONLDPresenter.CONTEXT_URL = 'http://foo.com/context.jsonld'
        request = testing.DummyRequest()

        result = views.read_jsonld(annotation, request)

        AnnotationJSONLDPresenter.assert_called_once_with(request, annotation)
        assert result == presenter.asdict()

    @pytest.fixture
    def AnnotationJSONLDPresenter(self, patch):
        return patch('h.api.views.AnnotationJSONLDPresenter')


@pytest.mark.usefixtures('AnnotationEvent',
                         'AnnotationJSONPresenter',
                         'schemas',
                         'storage')
class TestUpdate(object):

    def test_it_inits_the_schema(self, mock_request, schemas):
        annotation = mock.Mock()

        views.update(annotation, mock_request)

        schemas.UpdateAnnotationSchema.assert_called_once_with(
            mock_request,
            annotation.target_uri,
            annotation.groupid)

    def test_it_raises_if_json_parsing_fails(self, mock_request):
        """It raises PayloadError if parsing of the request body fails."""
        # Make accessing the request.json_body property raise ValueError.
        type(mock_request).json_body = mock.PropertyMock(
            side_effect=ValueError)

        with pytest.raises(views.PayloadError):
            views.update(mock.Mock(), mock_request)

    def test_it_validates_the_posted_data(self, mock_request, schemas):
        annotation = mock.Mock()
        schema = schemas.UpdateAnnotationSchema.return_value

        views.update(annotation, mock_request)

        schema.validate.assert_called_once_with(mock_request.json_body)

    def test_it_raises_if_validate_raises(self, mock_request, schemas):
        schemas.UpdateAnnotationSchema.return_value.validate\
            .side_effect = ValidationError('asplode')

        with pytest.raises(ValidationError):
            views.update(mock.Mock(), mock_request)

    def test_it_updates_the_annotation_in_storage(self,
                                                  mock_request,
                                                  storage,
                                                  schemas):
        annotation = mock.Mock()
        schema = schemas.UpdateAnnotationSchema.return_value
        schema.validate.return_value = mock.sentinel.validated_data

        views.update(annotation, mock_request)

        storage.update_annotation.assert_called_once_with(
            mock_request.db,
            annotation.id,
            mock.sentinel.validated_data
        )

    def test_it_raises_if_storage_raises(self, mock_request, storage):
        storage.update_annotation.side_effect = ValidationError('asplode')

        with pytest.raises(ValidationError):
            views.update(mock.Mock(), mock_request)

    def test_it_inits_an_AnnotationEvent(self,
                                         AnnotationEvent,
                                         storage,
                                         mock_request):
        annotation = mock.Mock()

        views.update(annotation, mock_request)

        AnnotationEvent.assert_called_once_with(
            mock_request, storage.update_annotation.return_value.id, 'update',
            annotation_dict=None)

    def test_it_fires_the_AnnotationEvent(self, AnnotationEvent, mock_request):
        views.update(mock.Mock(), mock_request)

        mock_request.notify_after_commit.assert_called_once_with(
            AnnotationEvent.return_value)

    def test_it_inits_a_presenter(self,
                                  AnnotationJSONPresenter,
                                  mock_request,
                                  storage):
        views.update(mock.Mock(), mock_request)

        AnnotationJSONPresenter.assert_any_call(
            mock_request, storage.update_annotation.return_value)

    def test_it_dictizes_the_presenter(self,
                                       AnnotationJSONPresenter,
                                       mock_request):
        views.update(mock.Mock(), mock_request)

        AnnotationJSONPresenter.return_value.asdict.assert_called_with()

    def test_it_returns_a_presented_dict(self,
                                         AnnotationJSONPresenter,
                                         mock_request):
        returned = views.update(mock.Mock(), mock_request)

        assert returned == (
            AnnotationJSONPresenter.return_value.asdict.return_value)

    @pytest.fixture
    def mock_request(self):
        return mock.Mock()


@pytest.mark.usefixtures('AnnotationEvent',
                         'AnnotationJSONPresenter',
                         'storage')
class TestDelete(object):

    def test_it_deletes_then_annotation_from_storage(self, storage):
        annotation = mock.Mock()
        request = mock.Mock()

        views.delete(annotation, request)

        storage.delete_annotation.assert_called_once_with(request.db,
                                                          annotation.id)

    def test_it_serializes_the_annotation(self, AnnotationJSONPresenter):
        annotation = mock.Mock()
        request = mock.Mock()

        views.delete(annotation, request)

        AnnotationJSONPresenter.assert_called_once_with(request, annotation)

    def test_it_inits_and_fires_an_AnnotationEvent(self,
                                                   AnnotationEvent,
                                                   AnnotationJSONPresenter):
        annotation = mock.Mock()
        request = mock.Mock()
        event = AnnotationEvent.return_value
        annotation_dict = AnnotationJSONPresenter.return_value.asdict.return_value

        views.delete(annotation, request)

        AnnotationEvent.assert_called_once_with(request, annotation.id, 'delete',
                                                annotation_dict=annotation_dict)
        request.notify_after_commit.assert_called_once_with(event)

    def test_it_returns_object(self):
        annotation = mock.Mock()
        request = mock.Mock()

        result = views.delete(annotation, request)

        assert result == {'id': annotation.id, 'deleted': True}


@pytest.fixture
def AnnotationEvent(patch):
    return patch('h.api.views.AnnotationEvent')


@pytest.fixture
def AnnotationJSONPresenter(patch):
    return patch('h.api.views.AnnotationJSONPresenter')


@pytest.fixture
def search_lib(patch):
    return patch('h.api.views.search_lib')


@pytest.fixture
def schemas(patch):
    return patch('h.api.views.schemas')


@pytest.fixture
def storage(patch):
    return patch('h.api.views.storage')
