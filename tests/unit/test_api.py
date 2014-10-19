# -*- coding: utf-8 -*-

"""Defines unit tests for h.api."""

from mock import call, patch, MagicMock
import pytest
from pyramid.testing import DummyRequest, DummyResource

from h import api

def test_index():
    """Get the API descriptor"""
    context = DummyResource()
    request = DummyRequest()

    result = api.index(context, request)

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


@patch('h.api.get_user')
@patch('h.api.Annotation')
def test_search(mock_Annotation, mock_get_user):
    params = {
        'offset': '3',
        'limit': '100',
        'uri': 'http://bla.test',
        'some_field': 'something',
    }
    search_results = mock_Annotation.search.return_value = MagicMock()
    count_result = mock_Annotation.count.return_value = MagicMock()
    user = mock_get_user.return_value = MagicMock()
    context = DummyResource()
    request = DummyRequest(params=params)

    result = api.search(context, request)

    kwargs = {
        'query': {
            'uri': 'http://bla.test',
            'some_field': 'something'
        },
        'offset': 3,
        'limit': 100,
        'user': user,
    }
    mock_Annotation.search.assert_called_once_with(**kwargs)
    mock_Annotation.count.assert_called_once_with(**kwargs)
    assert result['rows'] == search_results, "Search results should have been returned"
    assert result['total'] == count_result, "Total result count should have been returned"


@patch('h.api.get_user')
@patch('h.api.Annotation')
def test_annotations_index(mock_Annotation, mock_get_user):
    search_results = mock_Annotation.search.return_value = MagicMock()
    user = mock_get_user.return_value = MagicMock()
    context = DummyResource()
    request = DummyRequest()

    result = api.annotations_index(context, request)

    mock_Annotation.search.assert_called_once_with(user=user)
    assert result == search_results, "Search results should have been returned"


@patch('h.api.get_user')
@patch('h.api.Annotation')
def test_create(mock_Annotation, mock_get_user):
    annotation = mock_Annotation.return_value = MagicMock()
    user = mock_get_user.return_value = MagicMock()
    user.id = 'alice'
    user.consumer.key = 'real_consumer'
    context = DummyResource()
    request = DummyRequest(json_body=_json_annotation)
    request.registry = MagicMock()

    result = api.create(context, request)

    mock_Annotation.assert_called_once_with({'text': 'blabla', 'quote': 'blub'})
    annotation.__setitem__.assert_any_call('user', 'alice')
    annotation.__setitem__.assert_any_call('consumer', 'real_consumer')
    annotation.save.assert_called_once()

    assert request.registry.notify.call_count == 1, "Annotation event should have occured"
    assert request.registry.notify.call_args[0][0].action == 'create', "Annotation event action should be 'create'"


def test_read():
    context = DummyResource()
    request = DummyRequest()
    request.registry = MagicMock()

    result = api.read(context, request)

    assert request.registry.notify.call_count == 1, "Annotation event should have occured"
    assert request.registry.notify.call_args[0][0].action == 'read', "Annotation event action should be 'read'"
    assert result == context, "Annotation should have been returned"


def test_update():
    annotation = MagicMock()
    context = annotation
    request = DummyRequest(json_body=_json_annotation)
    request.registry = MagicMock()

    result = api.update(context, request)

    annotation.update.assert_called_once({'text':'blabla', 'quote':'blub'})
    annotation.save.assert_called_once()
    assert request.registry.notify.call_count == 1, "Annotation event should have occured"
    assert request.registry.notify.call_args[0][0].action == 'update', "Annotation event action should be 'update'"
    assert result == context, "Annotation should have been returned"


def test_update_anonymize_deletes():
    pass


def test_update_change_permissions():
    pass


def test_delete():
    pass


_json_annotation = {
    'text':'blabla',
    'quote': 'blub',
    'created': '2040-05-20',
    'updated': '2040-05-23',
    'user': 'eve',
    'consumer': 'fake_consumer',
    'id': '1337',
}
