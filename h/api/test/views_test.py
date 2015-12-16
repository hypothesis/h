# -*- coding: utf-8 -*-
"""Defines unit tests for h.api.views."""

import mock
import pytest

from pyramid import testing

from h.api import views


def _mock_annotation(**kwargs):
    """Return a mock h.api.resources.Annotation object."""
    annotation = mock.MagicMock()
    annotation.model = model = mock.MagicMock()
    model.__getitem__.side_effect = kwargs.__getitem__
    model.__setitem__.side_effect = kwargs.__setitem__
    model.get.side_effect = kwargs.get
    model.__contains__.side_effect = kwargs.__contains__
    return annotation


def test_error_not_found_sets_status_code():
    request = testing.DummyRequest()

    views.error_not_found(context=None, request=request)

    assert request.response.status_code == 404


def test_error_not_found_returns_status_object():
    request = testing.DummyRequest()

    result = views.error_not_found(context=None, request=request)

    assert result == {'status': 'failure', 'reason': 'not_found'}


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


def test_index():
    """Get the API descriptor"""
    result = views.index(testing.DummyResource(), testing.DummyRequest())

    # Pyramid's host url defaults to http://example.com
    host = 'http://example.com'
    links = result['links']
    assert links['annotation']['create']['method'] == 'POST'
    assert links['annotation']['create']['url'] == host + '/annotations'
    assert links['annotation']['delete']['method'] == 'DELETE'
    assert links['annotation']['delete']['url'] == host + '/annotations/:id'
    assert links['annotation']['read']['method'] == 'GET'
    assert links['annotation']['read']['url'] == host + '/annotations/:id'
    assert links['annotation']['update']['method'] == 'PUT'
    assert links['annotation']['update']['url'] == host + '/annotations/:id'
    assert links['search']['method'] == 'GET'
    assert links['search']['url'] == host + '/search'


def test_search_searches(search_lib):
    request = testing.DummyRequest()

    views.search(request)

    search_lib.search.assert_called_once_with(request,
                                              request.params,
                                              separate_replies=False)


def test_search_returns_search_results(search_lib):
    request = testing.DummyRequest()

    result = views.search(request)

    assert result == search_lib.search.return_value


def test_access_token_returns_create_token_response():
    """It should return request.create_token_response()."""
    request = mock.Mock()

    response_data = views.access_token(request)

    request.create_token_response.assert_called_with()
    assert response_data == request.create_token_response.return_value


# The fixtures required to mock all of annotator_token()'s dependencies.
annotator_token_fixtures = pytest.mark.usefixtures('access_token')


@annotator_token_fixtures
def test_annotator_token_sets_grant_type():
    request = mock.Mock()

    views.annotator_token(request)

    assert request.grant_type == 'client_credentials'


@annotator_token_fixtures
def test_annotator_token_calls_access_token(access_token):
    request = mock.Mock()

    views.annotator_token(request)

    access_token.assert_called_once_with(request)


@annotator_token_fixtures
def test_annotator_token_gets_access_token_from_response_json(access_token):
    response = access_token.return_value = mock.Mock()

    views.annotator_token(mock.Mock())

    response.json_body.get.assert_called_once_with('access_token', response)


def test_annotations_index_searches(search_lib):
    request = testing.DummyRequest()

    views.annotations_index(request)

    search_lib.search.assert_called_once_with(request, {"limit": 20})


def test_annotations_index_returns_search_results(search_lib):
    request = testing.DummyRequest()

    result = views.annotations_index(request)

    assert result == search_lib.search.return_value


# The fixtures required to mock all of create()'s dependencies.
create_fixtures = pytest.mark.usefixtures(
    'logic', 'AnnotationEvent', 'schemas')


@create_fixtures
def test_create_raises_if_json_parsing_fails():
    """The view raises PayloadError if parsing of the request body fails."""
    request = mock.Mock()

    # Make accessing the request.json_body property raise ValueError.
    type(request).json_body = mock.PropertyMock(side_effect=ValueError)

    with pytest.raises(views.PayloadError):
        views.update(mock.Mock(), request)


@create_fixtures
def test_create_calls_create_annotation(logic, schemas):
    """It should call logic.create_annotation() appropriately."""
    request = mock.Mock()
    schema = schemas.CreateAnnotationSchema.return_value
    schema.validate.return_value = {'foo': 123}

    views.create(request)

    logic.create_annotation.assert_called_once_with({'foo': 123})


@create_fixtures
def test_create_calls_validator(schemas):
    request = mock.Mock()
    schema = schemas.CreateAnnotationSchema.return_value

    views.create(request)

    schema.validate.assert_called_once_with(request.json_body)


@create_fixtures
def test_create_inits_AnnotationEvent_once(AnnotationEvent):
    views.create(mock.Mock())

    assert AnnotationEvent.call_count == 1


@create_fixtures
def test_create_event(AnnotationEvent, logic):
    request = mock.Mock()
    annotation = logic.create_annotation.return_value
    event = AnnotationEvent.return_value

    views.create(request)

    AnnotationEvent.assert_called_once_with == (request, annotation, 'create')
    request.registry.notify.assert_called_once_with(event)


@create_fixtures
def test_create_returns_annotation(logic):
    request = mock.Mock()
    result = views.create(request)

    assert result == logic.create_annotation.return_value


def test_read_returns_annotation():
    context = mock.Mock()
    request = mock.Mock()
    result = views.read(context, request)

    assert result == context.model


# The fixtures required to mock all of update()'s dependencies.
update_fixtures = pytest.mark.usefixtures(
    'logic', 'Annotation', 'schemas')


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
    request = mock.Mock()
    schema = schemas.UpdateAnnotationSchema.return_value

    views.update(mock.Mock(), request)

    schema.validate.assert_called_once_with(request.json_body)


@update_fixtures
def test_update_calls_update_annotation(logic, schemas):
    context = mock.Mock()
    request = mock.Mock()
    schema = schemas.UpdateAnnotationSchema.return_value
    schema.validate.return_value = {'foo': 123}

    views.update(context, request)

    logic.update_annotation.assert_called_once_with(context.model,
                                                    {'foo': 123})


@update_fixtures
def test_update_event(AnnotationEvent):
    request = mock.Mock()
    annotation = mock.Mock()
    event = AnnotationEvent.return_value
    views.update(annotation, request)
    AnnotationEvent.assert_called_once_with(request, annotation.model,
                                            'update')
    request.registry.notify.assert_called_once_with(event)


@update_fixtures
def test_update_returns_annotation():
    context = mock.Mock()
    request = mock.Mock()
    result = views.update(context, request)

    assert result == context.model


# The fixtures required to mock all of delete()'s dependencies.
delete_fixtures = pytest.mark.usefixtures('AnnotationEvent', 'logic')


@delete_fixtures
def test_delete_calls_delete_annotation(logic):
    annotation = mock.MagicMock()
    request = mock.Mock()

    views.delete(annotation, request)

    logic.delete_annotation.assert_called_once_with(annotation.model)


@delete_fixtures
def test_delete_event(AnnotationEvent):
    annotation = _mock_annotation(id='foo', group='test-group')
    request = mock.Mock(effective_principals=['group:test-group'])
    event = AnnotationEvent.return_value

    views.delete(annotation, request)

    AnnotationEvent.assert_called_once_with(request, annotation.model, 'delete')
    request.registry.notify.assert_called_once_with(event)


@delete_fixtures
def test_delete_returns_id():
    annotation = _mock_annotation(id='foo', group='test-group')

    response_data = views.delete(
        annotation, mock.Mock(effective_principals=['group:test-group']))

    assert response_data['id'] == annotation.model['id']


@delete_fixtures
def test_delete_returns_deleted():
    response_data = views.delete(
        _mock_annotation(id='foo', group='test-group'),
        mock.Mock(effective_principals=['group:test-group']))

    assert response_data['deleted'] is True


@delete_fixtures
def test_delete_does_not_crash_if_annotation_has_no_group():
    annotation = _mock_annotation(id='foo')
    assert 'group' not in annotation

    views.delete(
        annotation,
        mock.Mock(effective_principals=['group:test-group']))


@pytest.fixture
def search_lib(request):
    patcher = mock.patch('h.api.views.search_lib', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def AnnotationEvent(request):
    patcher = mock.patch('h.api.views.AnnotationEvent', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def Annotation(request):
    patcher = mock.patch('h.api.views.Annotation', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def logic(request):
    patcher = mock.patch('h.api.views.logic', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def _publish_annotation_event(request):
    patcher = mock.patch('h.api.views._publish_annotation_event',
                         autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def access_token(request):
    patcher = mock.patch('h.api.views.access_token', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def schemas(request):
    patcher = mock.patch('h.api.views.schemas', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
