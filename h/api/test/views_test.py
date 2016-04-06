# -*- coding: utf-8 -*-

import mock
import pytest

from pyramid import testing

from h.api import views


def test_error_api_sets_status_code_from_error():
    request = testing.DummyRequest()
    exc = views.APIError("it exploded", status_code=429)

    views.error_api(exc, request)

    assert request.response.status_code == 429


def test_error_api_returns_status_object():
    request = testing.DummyRequest()
    exc = views.APIError("it exploded", status_code=429)

    result = views.error_api(exc, request)

    assert result == {'status': 'failure', 'reason': 'it exploded'}


def test_error_validation_sets_bad_request_status_code():
    request = testing.DummyRequest()
    exc = mock.Mock(message="it exploded")

    views.error_validation(exc, request)

    assert request.response.status_code == 400


def test_error_validation_returns_status_object():
    request = testing.DummyRequest()
    exc = mock.Mock(message="it exploded")

    result = views.error_validation(exc, request)

    assert result == {'status': 'failure', 'reason': 'it exploded'}


@pytest.mark.usefixtures('routes_mapper')
def test_index(routes_mapper):
    """Get the API descriptor"""
    routes_mapper.add_route('api.search', '/dummy/search')
    routes_mapper.add_route('api.annotations', '/dummy/annotations')
    routes_mapper.add_route('api.annotation', '/dummy/annotations/:id')
    result = views.index(testing.DummyResource(), testing.DummyRequest())

    # Pyramid's host url defaults to http://example.com
    host = 'http://example.com'
    links = result['links']
    assert links['annotation']['create']['method'] == 'POST'
    assert links['annotation']['create']['url'] == host + '/dummy/annotations'
    assert links['annotation']['delete']['method'] == 'DELETE'
    assert links['annotation']['delete']['url'] == host + '/dummy/annotations/:id'
    assert links['annotation']['read']['method'] == 'GET'
    assert links['annotation']['read']['url'] == host + '/dummy/annotations/:id'
    assert links['annotation']['update']['method'] == 'PUT'
    assert links['annotation']['update']['url'] == host + '/dummy/annotations/:id'
    assert links['search']['method'] == 'GET'
    assert links['search']['url'] == host + '/dummy/search'


def test_search_searches(search_lib):
    request = testing.DummyRequest()

    views.search(request)

    search_lib.search.assert_called_once_with(request,
                                              request.params,
                                              separate_replies=False)


def test_search_returns_search_results(search_lib):
    request = testing.DummyRequest()
    search_lib.search.return_value = {'total': 0, 'rows': []}

    result = views.search(request)

    assert result == {'total': 0, 'rows': []}


def test_search_presents_annotations(search_lib, AnnotationJSONPresenter):
    request = testing.DummyRequest()
    search_lib.search.return_value = {'total': 2, 'rows': [{'foo': 'bar'},
                                                           {'baz': 'bat'}]}
    presenter = AnnotationJSONPresenter.return_value
    presenter.asdict.return_value = {'giraffe': True}

    result = views.search(request)

    assert result == {'total': 2, 'rows': [{'giraffe': True},
                                           {'giraffe': True}]}


def test_search_presents_replies(search_lib, AnnotationJSONPresenter):
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


create_fixtures = pytest.mark.usefixtures('AnnotationEvent',
                                          'AnnotationJSONPresenter',
                                          'schemas',
                                          'storage')


@create_fixtures
def test_create_raises_if_json_parsing_fails():
    """The view raises PayloadError if parsing of the request body fails."""
    request = mock.Mock()

    # Make accessing the request.json_body property raise ValueError.
    type(request).json_body = mock.PropertyMock(side_effect=ValueError)

    with pytest.raises(views.PayloadError):
        views.update(mock.Mock(), request)


@create_fixtures
def test_create_calls_create_annotation(storage, schemas):
    """It should call storage.create_annotation() appropriately."""
    request = mock.Mock()
    schema = schemas.LegacyCreateAnnotationSchema.return_value
    schema.validate.return_value = {'foo': 123}

    views.create(request)

    storage.create_annotation.assert_called_once_with(request, {'foo': 123})


@create_fixtures
def test_create_calls_validator(schemas, copy):
    request = mock.Mock()
    copy.deepcopy.side_effect = lambda x: x
    schema = schemas.LegacyCreateAnnotationSchema.return_value

    views.create(request)

    schema.validate.assert_called_once_with(request.json_body)


@create_fixtures
def test_create_event(AnnotationEvent, storage):
    request = mock.Mock()
    annotation = storage.create_annotation.return_value
    event = AnnotationEvent.return_value

    views.create(request)

    AnnotationEvent.assert_called_once_with(request, annotation, 'create')
    request.registry.notify.assert_called_once_with(event)


@create_fixtures
def test_create_returns_presented_annotation(AnnotationJSONPresenter, storage):
    request = mock.Mock()
    presenter = mock.Mock()
    AnnotationJSONPresenter.return_value = presenter

    result = views.create(request)

    AnnotationJSONPresenter.assert_called_once_with(
            request,
            storage.create_annotation.return_value)
    assert result == presenter.asdict()


def test_read_returns_presented_annotation(AnnotationJSONPresenter):
    annotation = mock.Mock()
    request = mock.Mock()
    presenter = mock.Mock()
    AnnotationJSONPresenter.return_value = presenter

    result = views.read(annotation, request)

    AnnotationJSONPresenter.assert_called_once_with(request, annotation)
    assert result == presenter.asdict()


update_fixtures = pytest.mark.usefixtures('AnnotationEvent',
                                          'AnnotationJSONPresenter',
                                          'schemas',
                                          'storage')


@update_fixtures
def test_update_raises_if_json_parsing_fails():
    """The view raises PayloadError if parsing of the request body fails."""
    request = mock.Mock()

    # Make accessing the request.json_body property raise ValueError.
    type(request).json_body = mock.PropertyMock(side_effect=ValueError)

    with pytest.raises(views.PayloadError):
        views.update(mock.Mock(), request)


@update_fixtures
def test_update_calls_validator(schemas):
    annotation = mock.Mock()
    request = mock.Mock()
    schema = schemas.UpdateAnnotationSchema.return_value

    views.update(annotation, request)

    schema.validate.assert_called_once_with(request.json_body)


@update_fixtures
def test_update_calls_update_annotation(storage, schemas):
    annotation = mock.Mock()
    request = mock.Mock()
    schema = schemas.UpdateAnnotationSchema.return_value
    schema.validate.return_value = {'foo': 123}

    views.update(annotation, request)

    storage.update_annotation.assert_called_once_with(request,
                                                      annotation.id,
                                                      {'foo': 123})


@update_fixtures
def test_update_returns_presented_annotation(AnnotationJSONPresenter, storage):
    annotation = mock.Mock()
    request = mock.Mock()
    presenter = mock.Mock()
    AnnotationJSONPresenter.return_value = presenter

    result = views.update(annotation, request)

    AnnotationJSONPresenter.assert_called_once_with(
            request,
            storage.update_annotation.return_value)
    assert result == presenter.asdict()


@update_fixtures
def test_update_event(AnnotationEvent, storage):
    annotation = mock.Mock()
    request = mock.Mock()
    event = AnnotationEvent.return_value
    annotation_out = storage.update_annotation.return_value

    views.update(annotation, request)

    AnnotationEvent.assert_called_once_with(request, annotation_out, 'update')
    request.registry.notify.assert_called_once_with(event)


delete_fixtures = pytest.mark.usefixtures('AnnotationEvent', 'storage')


@delete_fixtures
def test_delete_calls_delete_annotation(storage):
    annotation = mock.Mock()
    request = mock.Mock()

    views.delete(annotation, request)

    storage.delete_annotation.assert_called_once_with(request, annotation.id)


@delete_fixtures
def test_delete_event(AnnotationEvent):
    annotation = mock.Mock()
    request = mock.Mock()
    event = AnnotationEvent.return_value

    views.delete(annotation, request)

    AnnotationEvent.assert_called_once_with(request, annotation, 'delete')
    request.registry.notify.assert_called_once_with(event)


@delete_fixtures
def test_delete_returns_object():
    annotation = mock.Mock()
    request = mock.Mock()

    result = views.delete(annotation, request)

    assert result == {'id': annotation.id, 'deleted': True}


@pytest.fixture
def AnnotationEvent(request):
    patcher = mock.patch('h.api.views.AnnotationEvent', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def AnnotationJSONPresenter(request):
    patcher = mock.patch('h.api.views.AnnotationJSONPresenter', autospec=True)
    cls = patcher.start()
    request.addfinalizer(patcher.stop)
    return cls


@pytest.fixture
def copy(request):
    patcher = mock.patch('h.api.views.copy', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def search_lib(request):
    patcher = mock.patch('h.api.views.search_lib', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def schemas(request):
    patcher = mock.patch('h.api.views.schemas', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def storage(request):
    patcher = mock.patch('h.api.views.storage', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def _publish_annotation_event(request):
    patcher = mock.patch('h.api.views._publish_annotation_event',
                         autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
