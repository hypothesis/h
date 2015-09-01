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


# The fixtures required to mock all of search()'s dependencies.
search_fixtures = pytest.mark.usefixtures('auth', 'search_lib')


@search_fixtures
def test_search_calls_get_user(auth):
    """It should call get_user() once passing the request."""
    request = mock.Mock()

    views.search(request)

    auth.get_user.assert_called_once_with(request)


@search_fixtures
def test_search_calls_search(search_lib):
    """It should call search_lib.search() once."""
    views.search(mock.Mock())

    assert search_lib.search.call_count == 1


@search_fixtures
def test_search_passes_effective_principals_to_search_lib(search_lib):
    request = mock.Mock()

    views.search(request)

    assert search_lib.search.call_args[1]['effective_principals'] == (
        request.effective_principals)


@search_fixtures
def test_search_passes_params_to_search(search_lib):
    """It should pass request.params to search_lib.search()."""
    request = mock.Mock()

    views.search(request)

    assert search_lib.search.call_args[1]['request_params'] == request.params


@search_fixtures
def test_search_passes_user_to_search(auth, search_lib):
    """It should pass the user from get_user() to search_lib.search()."""
    views.search(mock.Mock())

    assert search_lib.search.call_args[1]['user'] == auth.get_user.return_value


@search_fixtures
def test_search_calls_feature():
    """It should call request.feature() once, passing 'search_normalized'."""
    request = mock.Mock()

    views.search(request)

    request.feature.assert_called_once_with('search_normalized')


@search_fixtures
def test_search_passes_search_normalized_uris(search_lib):
    """It should pass search_normalized from request.feature() to search()."""
    request = mock.Mock()

    views.search(request)

    assert search_lib.search.call_args[1]['search_normalized_uris'] == (
        request.feature.return_value)


@search_fixtures
def test_search_returns_total(search_lib):
    """It should return the total from search_lib.search()."""
    search_lib.search.return_value = {
        'total': 3,
        # In production these would be annotation dicts, not strings.
        'rows': ['annotation_1', 'annotation_2', 'annotation_3']
    }

    response_data = views.search(mock.Mock())

    assert response_data['total'] == 3


@search_fixtures
def test_search_returns_rendered_annotations(search_lib):
    """It should return the rendered annotations.

    It should pass the annotations from search_lib.search() through
    search_lib.render() and return the results.

    """
    search_lib.search.return_value = {
        'total': 3,
        # In production these would be annotation dicts, not strings.
        'rows': ['annotation_1', 'annotation_2', 'annotation_3']
    }
    # Our mock render function just appends '_rendered' onto our mock
    # annotation strings.
    search_lib.render.side_effect = lambda annotation: annotation + '_rendered'

    response_data = views.search(mock.Mock())

    assert response_data['rows'] == [
        'annotation_1_rendered', 'annotation_2_rendered',
        'annotation_3_rendered']


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


# The fixtures required to mock all of annotations_index()'s dependencies.
annotations_index_fixtures = pytest.mark.usefixtures('auth', 'search_lib')


@annotations_index_fixtures
def test_annotations_index_calls_get_user(auth):
    """It should call get_user() once passing the request."""
    request = mock.Mock()

    views.annotations_index(request)

    auth.get_user.assert_called_once_with(request)


@annotations_index_fixtures
def test_annotations_index_calls_index(search_lib):
    """It should call search_lib.index() once."""
    views.annotations_index(mock.Mock())

    assert search_lib.index.call_count == 1


@annotations_index_fixtures
def test_annotations_index_passes_user_to_index(auth, search_lib):
    """It should pass the user from get_user() to search_lib.index()."""
    views.annotations_index(mock.Mock())

    assert search_lib.index.call_args[1]['user'] == auth.get_user.return_value


@annotations_index_fixtures
def test_annotations_index_calls_feature():
    """It should call request.feature() once, passing 'search_normalized'."""
    request = mock.Mock()

    views.annotations_index(request)

    request.feature.assert_called_once_with('search_normalized')


@annotations_index_fixtures
def test_annotations_index_passes_search_normalized_uris(search_lib):
    """It should pass search_normalized from request.feature() to index()."""
    request = mock.Mock()

    views.annotations_index(request)

    assert search_lib.index.call_args[1]['search_normalized_uris'] == (
        request.feature.return_value)


@annotations_index_fixtures
def test_annotations_index_returns_total(search_lib):
    """It should return the total from search_lib.index()."""
    search_lib.index.return_value = {
        'total': 3,
        # In production these would be annotation dicts, not strings.
        'rows': ['annotation_1', 'annotation_2', 'annotation_3']
    }

    response_data = views.annotations_index(mock.Mock())

    assert response_data['total'] == 3


@annotations_index_fixtures
def test_annotations_index_returns_rendered_annotations(search_lib):
    """It should return the rendered annotations.

    It should pass the annotations from search_lib.index() through
    search_lib.render() and return the results.

    """
    search_lib.index.return_value = {
        'total': 3,
        # In production these would be annotation dicts, not strings.
        'rows': ['annotation_1', 'annotation_2', 'annotation_3']
    }
    # Our mock render function just appends '_rendered' onto our mock
    # annotation strings.
    search_lib.render.side_effect = lambda annotation: annotation + '_rendered'

    response_data = views.annotations_index(mock.Mock())

    assert response_data['rows'] == [
        'annotation_1_rendered', 'annotation_2_rendered',
        'annotation_3_rendered']


# The fixtures required to mock all of create()'s dependencies.
create_fixtures = pytest.mark.usefixtures(
    'auth', 'logic', 'AnnotationEvent', 'search_lib')


@create_fixtures
def test_create_returns_error_if_parsing_json_fails():
    """It should return an error if JSON parsing of the request body fails."""
    request = mock.Mock()
    # Make accessing the request.json_body property raise ValueError.
    type(request).json_body = mock.PropertyMock(side_effect=ValueError)

    error = views.create(request)

    assert error['status'] == 'failure'


@create_fixtures
def test_create_calls_logic(logic, auth):
    """It should call logic.create_annotation() appropriately."""
    request = mock.Mock()

    views.create(request)

    logic.create_annotation.assert_called_once_with(
        fields=request.json_body, user=auth.get_user.return_value)


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
def test_create_passes_user_to_create_annotation(auth, logic):
    """It should pass the user from get_user() to logic.create_annotation()."""
    views.create(mock.Mock())

    assert logic.create_annotation.call_args[1]['user'] == (
        auth.get_user.return_value)


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


# The fixtures required to mock all of update()'s dependencies.
update_fixtures = pytest.mark.usefixtures(
    'auth', 'logic', 'Annotation', 'search_lib')


@update_fixtures
def test_update_returns_error_if_json_parsing_fails():
    request = mock.Mock()
    # Make accessing the request.json_body property raise ValueError.
    type(request).json_body = mock.PropertyMock(side_effect=ValueError)

    error = views.update(mock.Mock(), request)

    assert error['status'] == 'failure'


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
    annotation = _mock_annotation(id='foo')
    request = mock.Mock()
    event = AnnotationEvent.return_value

    views.delete(annotation, request)

    AnnotationEvent.assert_called_once_with(request, annotation, 'delete')
    request.registry.notify.assert_called_once_with(event)


@delete_fixtures
def test_delete_returns_id():
    annotation = _mock_annotation(id='foo')
    request = mock.Mock()

    response_data = views.delete(annotation, request)

    assert response_data['id'] == annotation['id']


@delete_fixtures
def test_delete_returns_deleted():
    annotation = _mock_annotation(id='foo')
    request = mock.Mock()

    response_data = views.delete(annotation, request)

    assert response_data['deleted'] is True


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
def auth(request):
    patcher = mock.patch('h.api.views.auth', autospec=True)
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
