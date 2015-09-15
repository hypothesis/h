# -*- coding: utf-8 -*-
"""Defines unit tests for h.api.views."""

import mock
import pytest
from pyramid import testing
from pyramid import httpexceptions

from h import api
from h.api import views


def _mock_annotation(**kwargs):
    """Return a mock h.api.models.Annotation object."""
    annotation = mock.MagicMock()
    annotation.__getitem__.side_effect = kwargs.__getitem__
    annotation.__setitem__.side_effect = kwargs.__setitem__
    annotation.get.side_effect = kwargs.get
    annotation.__contains__.side_effect = kwargs.__contains__
    return annotation


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

    search_lib.search.assert_called_once_with(request, request.params)


def test_search_renders_results(search_lib):
    request = testing.DummyRequest()
    search_lib.search.return_value = {
        'total': 3,
        'rows': ['a', 'b', 'c'],
    }
    search_lib.render.side_effect = lambda x: x.upper()

    result = views.search(request)

    assert result == {
        'total': 3,
        'rows': ['A', 'B', 'C'],
    }


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


def test_annotations_index_renders_results(search_lib):
    request = testing.DummyRequest()
    search_lib.search.return_value = {
        'total': 3,
        'rows': ['a', 'b', 'c'],
    }
    search_lib.render.side_effect = lambda x: x.upper()

    result = views.annotations_index(request)

    assert result == {
        'total': 3,
        'rows': ['A', 'B', 'C'],
    }


# The fixtures required to mock all of create()'s dependencies.
create_fixtures = pytest.mark.usefixtures(
    'get_user', 'logic', 'AnnotationEvent', 'search_lib')


@create_fixtures
def test_create_returns_error_if_parsing_json_fails():
    """It should return an error if JSON parsing of the request body fails."""
    request = mock.Mock()
    # Make accessing the request.json_body property raise ValueError.
    type(request).json_body = mock.PropertyMock(side_effect=ValueError)

    error = views.create(request)

    assert error['status'] == 'failure'


@create_fixtures
def test_create_calls_logic(logic, get_user):
    """It should call logic.create_annotation() appropriately."""
    request = mock.Mock()

    views.create(request)

    logic.create_annotation.assert_called_once_with(
        fields=request.json_body, user=get_user.return_value)


@create_fixtures
def test_create_calls_create_annotation_once(logic):
    """It should call logic.create_annotation() exactly once."""
    request = mock.Mock()

    views.create(request)

    assert logic.create_annotation.call_count == 1


@create_fixtures
def test_create_passes_json_to_create_annotation(logic):
    """It should pass the JSON from the request to create_annotation()."""
    request = mock.Mock()

    views.create(request)

    assert logic.create_annotation.call_args[1]['fields'] == request.json_body


@create_fixtures
def test_create_passes_user_to_create_annotation(get_user, logic):
    """It should pass the user from get_user() to logic.create_annotation()."""
    views.create(mock.Mock())

    assert logic.create_annotation.call_args[1]['user'] == (
        get_user.return_value)


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
def test_create_passes_annotation_to_render(logic, search_lib):
    views.create(mock.Mock())

    search_lib.render.assert_called_once_with(
        logic.create_annotation.return_value)


@create_fixtures
def test_create_returns_render(search_lib):
    """It should return what render() returns."""
    assert views.create(mock.Mock()) == search_lib.render.return_value


# The fixtures required to mock all of read()'s dependencies.
read_fixtures = pytest.mark.usefixtures('search_lib', 'AnnotationEvent')


@read_fixtures
def test_read_event(AnnotationEvent):
    annotation = _mock_annotation()
    request = mock.Mock(effective_principals=[])
    event = AnnotationEvent.return_value

    views.read(annotation, request)

    AnnotationEvent.assert_called_once_with(request, annotation, 'read')
    request.registry.notify.assert_called_once_with(event)


@read_fixtures
def test_read_calls_render(search_lib):
    annotation = _mock_annotation()

    views.read(context=annotation,
               request=mock.Mock(effective_principals=[]))

    search_lib.render.assert_called_once_with(annotation)


@read_fixtures
def test_read_returns_rendered_annotation(search_lib):
    response_data = views.read(
        _mock_annotation(),
        mock.Mock(effective_principals=[]))

    assert response_data == search_lib.render.return_value


@read_fixtures
def test_read_does_not_crash_if_annotation_has_no_group():
    annotation = _mock_annotation()
    assert 'group' not in annotation

    views.read(annotation, mock.Mock(effective_principals=[]))


# The fixtures required to mock all of update()'s dependencies.
update_fixtures = pytest.mark.usefixtures('logic', 'Annotation', 'search_lib')


@update_fixtures
def test_update_returns_error_if_json_parsing_fails():
    request = mock.Mock()
    # Make accessing the request.json_body property raise ValueError.
    type(request).json_body = mock.PropertyMock(side_effect=ValueError)

    error = views.update(mock.Mock(), request)

    assert error['status'] == 'failure'


@update_fixtures
def test_update_calls_has_permission():
    annotation = mock.Mock()
    request = mock.Mock()

    views.update(annotation, request)

    request.has_permission.assert_called_once_with('admin', annotation)


@update_fixtures
def test_update_calls_update_annotation_once(logic):
    views.update(mock.Mock(), mock.Mock())

    assert logic.update_annotation.call_count == 1


@update_fixtures
def test_update_passes_annotation_to_update_annotation(logic):
    annotation = mock.Mock()

    views.update(annotation, mock.Mock())

    assert logic.update_annotation.call_args[0][0] == annotation


@update_fixtures
def test_update_passes_fields_to_update_annotation(logic):
    request = mock.Mock()

    views.update(mock.Mock(), request)

    assert logic.update_annotation.call_args[0][1] == request.json_body


@update_fixtures
def test_update_passes_has_admin_permission_to_update_annotation(logic):
    request = mock.Mock()

    views.update(mock.Mock(), request)

    assert logic.update_annotation.call_args[0][2] == (
        request.has_permission.return_value)


@update_fixtures
def test_update_returns_error_if_update_annotation_raises(logic):
    logic.update_annotation.side_effect = RuntimeError("Nope", 401)

    error = views.update(mock.Mock(), mock.Mock())

    assert error['status'] == 'failure'


@update_fixtures
def test_update_event(AnnotationEvent):
    request = mock.Mock()
    annotation = mock.Mock()
    event = AnnotationEvent.return_value
    views.update(annotation, request)
    AnnotationEvent.assert_called_once_with(request, annotation, 'update')
    request.registry.notify.assert_called_once_with(event)


@update_fixtures
def test_update_calls_render(search_lib):
    annotation = mock.Mock()

    views.update(annotation, mock.Mock())

    search_lib.render.assert_called_once_with(annotation)


@update_fixtures
def test_update_returns_rendered_annotation(search_lib):
    assert views.update(mock.Mock(), mock.Mock()) == (
        search_lib.render.return_value)


# The fixtures required to mock all of delete()'s dependencies.
delete_fixtures = pytest.mark.usefixtures('AnnotationEvent', 'logic')


@delete_fixtures
def test_delete_calls_delete_annotation(logic):
    annotation = mock.MagicMock()
    request = mock.Mock()

    views.delete(annotation, request)

    logic.delete_annotation.assert_called_once_with(annotation)


@delete_fixtures
def test_delete_event(AnnotationEvent):
    annotation = _mock_annotation(id='foo', group='test-group')
    request = mock.Mock(effective_principals=['group:test-group'])
    event = AnnotationEvent.return_value

    views.delete(annotation, request)

    AnnotationEvent.assert_called_once_with(request, annotation, 'delete')
    request.registry.notify.assert_called_once_with(event)


@delete_fixtures
def test_delete_returns_id():
    annotation = _mock_annotation(id='foo', group='test-group')

    response_data = views.delete(
        annotation, mock.Mock(effective_principals=['group:test-group']))

    assert response_data['id'] == annotation['id']


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
def search_render(request):
    patcher = mock.patch('h.api.search.render', autospec=True)
    func = patcher.start()
    request.addfinalizer(patcher.stop)
    func.side_effect = lambda x: x
    return func


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
def get_user(request):
    patcher = mock.patch('h.api.views.get_user', autospec=True)
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
