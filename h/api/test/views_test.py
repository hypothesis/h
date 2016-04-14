# -*- coding: utf-8 -*-

import mock
import pytest

from pyramid import testing

from h.api import views


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

    def test_it_returns_status_object(self):
        request = testing.DummyRequest()
        exc = mock.Mock(message="it exploded")

        result = views.error_validation(exc, request)

        assert result == {'status': 'failure', 'reason': 'it exploded'}


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


@pytest.mark.usefixtures('search_lib', 'AnnotationJSONPresenter')
class TestSearch(object):

    def test_it_searches(self, search_lib):
        request = testing.DummyRequest()

        views.search(request)

        search_lib.search.assert_called_once_with(request,
                                                  request.params,
                                                  separate_replies=False)

    def test_it_returns_search_results(self, search_lib):
        request = testing.DummyRequest()
        search_lib.search.return_value = {'total': 0, 'rows': []}

        result = views.search(request)

        assert result == {'total': 0, 'rows': []}

    def test_it_presents_annotations(self,
                                     search_lib,
                                     AnnotationJSONPresenter):
        request = testing.DummyRequest()
        search_lib.search.return_value = {'total': 2, 'rows': [{'foo': 'bar'},
                                                               {'baz': 'bat'}]}
        presenter = AnnotationJSONPresenter.return_value
        presenter.asdict.return_value = {'giraffe': True}

        result = views.search(request)

        assert result == {'total': 2, 'rows': [{'giraffe': True},
                                               {'giraffe': True}]}

    def test_it_presents_replies(self, search_lib, AnnotationJSONPresenter):
        request = testing.DummyRequest(params={'_separate_replies': '1'})
        search_lib.search.return_value = {'total': 1,
                                          'rows': [{'foo': 'bar'}],
                                          'replies': [{'baz': 'bat'},
                                                      {'baz': 'bat'}]}
        presenter = AnnotationJSONPresenter.return_value
        presenter.asdict.return_value = {'giraffe': True}

        result = views.search(request)

        assert result == {'total': 1,
                          'rows': [{'giraffe': True}],
                          'replies': [{'giraffe': True},
                                      {'giraffe': True}]}

    @pytest.fixture
    def search_lib(self, patch):
        return patch('h.api.views.search_lib')


@pytest.mark.usefixtures('AnnotationEvent',
                         'AnnotationJSONPresenter',
                         'copy',
                         'schemas',
                         'storage')
class TestCreateLegacy(object):

    """Tests for create() when the 'postgres' feature flag is off."""

    def test_it_raises_if_json_parsing_fails(self):
        """It raises PayloadError if parsing of the request body fails."""
        request = self.mock_request()

        # Make accessing the request.json_body property raise ValueError.
        type(request).json_body = mock.PropertyMock(side_effect=ValueError)

        with pytest.raises(views.PayloadError):
            views.create(request)

    def test_it_calls_legacy_create_annotation(self, storage, schemas):
        request = self.mock_request()
        schema = schemas.LegacyCreateAnnotationSchema.return_value
        schema.validate.return_value = {'foo': 123}

        views.create(request)

        storage.legacy_create_annotation.assert_called_once_with(request,
                                                                 {'foo': 123})

    def test_it_calls_validator(self, schemas, copy):
        request = self.mock_request()
        copy.deepcopy.side_effect = lambda x: x
        schema = schemas.LegacyCreateAnnotationSchema.return_value

        views.create(request)

        schema.validate.assert_called_once_with(request.json_body)

    def test_it_inits_AnnotationJSONPresenter(self,
                                              AnnotationJSONPresenter,
                                              storage):
        request = self.mock_request()

        views.create(request)

        AnnotationJSONPresenter.assert_called_once_with(
            request, storage.legacy_create_annotation.return_value)

    def test_it_publishes_annotation_event(self,
                                           AnnotationEvent,
                                           storage):
        """It publishes an annotation "create" event for the annotation."""
        request = self.mock_request()

        views.create(request)

        AnnotationEvent.assert_called_once_with(
            request,
            storage.legacy_create_annotation.return_value,
            'create')
        request.registry.notify.assert_called_once_with(
            AnnotationEvent.return_value)

    def test_it_returns_presented_annotation(self,
                                             AnnotationJSONPresenter,
                                             storage):
        request = self.mock_request()

        result = views.create(request)

        AnnotationJSONPresenter.assert_called_once_with(
            request,
            storage.legacy_create_annotation.return_value)
        assert result == (
            AnnotationJSONPresenter.return_value.asdict.return_value)

    def mock_request(self):
        return mock.Mock(feature=mock.Mock(return_value=False))

    @pytest.fixture
    def copy(self, patch):
        return patch('h.api.views.copy')


@pytest.mark.usefixtures('AnnotationEvent',
                         'AnnotationJSONPresenter',
                         'copy',
                         'schemas',
                         'storage')
class TestCreate(object):

    def test_it_raises_if_json_parsing_fails(self):
        """It raises PayloadError if parsing of the request body fails."""
        request = self.mock_request()

        # Make accessing the request.json_body property raise ValueError.
        type(request).json_body = mock.PropertyMock(side_effect=ValueError)

        with pytest.raises(views.PayloadError):
            views.create(request)

    def test_it_inits_CreateAnnotationSchema(self, schemas):
        request = self.mock_request()

        views.create(request)

        schemas.CreateAnnotationSchema.assert_called_once_with(request)

    def test_it_calls_schema_validate(self, copy, schemas):
        """It should call validate() with a deep copy of json_body."""
        copy.deepcopy.side_effect = [mock.sentinel.first_copy,
                                     mock.sentinel.second_copy]
        request = self.mock_request()

        views.create(request)

        assert copy.deepcopy.call_args_list[0] == mock.call(request.json_body)
        schemas.CreateAnnotationSchema.return_value.validate\
            .assert_called_once_with(mock.sentinel.first_copy)

    def test_it_calls_create_annotation(self, storage, schemas):
        request = self.mock_request()
        schema = schemas.CreateAnnotationSchema.return_value

        views.create(request)

        storage.create_annotation.assert_called_once_with(
            request, schema.validate.return_value)

    def test_it_inits_LegacyCreateAnnotationSchema(self, schemas):
        request = self.mock_request()

        views.create(request)

        schemas.LegacyCreateAnnotationSchema.assert_called_once_with(request)

    def test_it_calls_legacy_schema_validate(self, copy, schemas):
        """It should call validate() with a deep copy of json_body."""
        copy.deepcopy.side_effect = [mock.sentinel.first_copy,
                                     mock.sentinel.second_copy]
        request = self.mock_request()

        views.create(request)

        assert copy.deepcopy.call_args_list[0] == mock.call(request.json_body)
        schemas.LegacyCreateAnnotationSchema.return_value.validate\
            .assert_called_once_with(mock.sentinel.second_copy)

    def test_it_calls_legacy_create_annotation(self, storage, schemas):
        """It should call storage.create_annotation() appropriately."""
        request = self.mock_request()
        schema = schemas.LegacyCreateAnnotationSchema.return_value

        views.create(request)

        storage.legacy_create_annotation.assert_called_once_with(
            request,
            schema.validate.return_value)

    def test_it_reuses_the_postgres_annotation_id_in_elasticsearch(self,
                                                                   schemas,
                                                                   storage):
        request = self.mock_request()
        schema = schemas.LegacyCreateAnnotationSchema.return_value
        schema.validate.return_value = {'foo': 123}

        views.create(request)

        assert storage.legacy_create_annotation.call_args[0][1]['id'] == (
            storage.create_annotation.return_value.id)

    def test_it_inits_AnnotationJSONPresenter(self,
                                              AnnotationJSONPresenter,
                                              storage):
        request = self.mock_request()

        views.create(request)

        AnnotationJSONPresenter.assert_called_once_with(
            request, storage.create_annotation.return_value)

    def test_it_publishes_annotation_event(self,
                                           AnnotationEvent,
                                           storage):
        """It publishes an annotation "create" event for the annotation."""
        request = self.mock_request()

        views.create(request)

        AnnotationEvent.assert_called_once_with(
            request,
            storage.create_annotation.return_value,
            'create')
        request.registry.notify.assert_called_once_with(
            AnnotationEvent.return_value)

    def test_it_returns_presented_annotation(self,
                                             AnnotationJSONPresenter,
                                             storage):
        request = self.mock_request()

        result = views.create(request)

        AnnotationJSONPresenter.return_value.asdict.assert_called_once_with()
        assert result == (
            AnnotationJSONPresenter.return_value.asdict.return_value)

    def mock_request(self):
        return mock.Mock(feature=mock.Mock(return_value=True))

    @pytest.fixture
    def copy(self, patch):
        return patch('h.api.views.copy')


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

    def test_it_raises_if_json_parsing_fails(self):
        """It raises PayloadError if parsing of the request body fails."""
        request = mock.Mock()

        # Make accessing the request.json_body property raise ValueError.
        type(request).json_body = mock.PropertyMock(side_effect=ValueError)

        with pytest.raises(views.PayloadError):
            views.update(mock.Mock(), request)

    def test_it_calls_validator(self, schemas):
        annotation = mock.Mock()
        request = mock.Mock()
        schema = schemas.LegacyUpdateAnnotationSchema.return_value

        views.update(annotation, request)

        schema.validate.assert_called_once_with(request.json_body)

    def test_it_calls_update_annotation(self, storage, schemas):
        annotation = mock.Mock()
        request = mock.Mock()
        schema = schemas.LegacyUpdateAnnotationSchema.return_value
        schema.validate.return_value = {'foo': 123}

        views.update(annotation, request)

        storage.update_annotation.assert_called_once_with(request,
                                                          annotation.id,
                                                          {'foo': 123})

    def test_it_returns_presented_annotation(self,
                                             AnnotationJSONPresenter,
                                             storage):
        annotation = mock.Mock()
        request = mock.Mock()
        presenter = mock.Mock()
        AnnotationJSONPresenter.return_value = presenter

        result = views.update(annotation, request)

        AnnotationJSONPresenter.assert_called_once_with(
            request,
            storage.update_annotation.return_value)
        assert result == presenter.asdict()

    def test_it_calls_notify_with_an_event(self, AnnotationEvent, storage):
        annotation = mock.Mock()
        request = mock.Mock()
        event = AnnotationEvent.return_value
        annotation_out = storage.update_annotation.return_value

        views.update(annotation, request)

        AnnotationEvent.assert_called_once_with(request,
                                                annotation_out,
                                                'update')
        request.registry.notify.assert_called_once_with(event)


@pytest.mark.usefixtures('AnnotationEvent',
                         'AnnotationJSONPresenter',
                         'storage')
class TestDelete(object):

    def test_it_calls_delete_annotation(self, storage):
        annotation = mock.Mock()
        request = mock.Mock()

        views.delete(annotation, request)

        storage.delete_annotation.assert_called_once_with(request,
                                                          annotation.id)

    def test_it_calls_notify_with_an_event(self, AnnotationEvent):
        annotation = mock.Mock()
        request = mock.Mock()
        event = AnnotationEvent.return_value

        views.delete(annotation, request)

        AnnotationEvent.assert_called_once_with(request, annotation, 'delete')
        request.registry.notify.assert_called_once_with(event)

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
def copy(patch):
    return patch('h.api.views.copy')


@pytest.fixture
def search_lib(patch):
    return patch('h.api.views.search_lib')


@pytest.fixture
def schemas(patch):
    return patch('h.api.views.schemas')


@pytest.fixture
def storage(patch):
    return patch('h.api.views.storage')
