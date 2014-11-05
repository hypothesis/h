# -*- coding: utf-8 -*-

"""Defines unit tests for h.api."""

from mock import call, patch, MagicMock
import pytest
from pyramid.testing import DummyRequest, DummyResource

from h import api

from helpers import DictMock


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


def test_search_parameters():
    request_params = {
        'offset': '3',
        'limit': '100',
        'uri': 'http://bla.test',
        'some_field': 'something',
    }
    user = object()
    assert api._search_params(request_params, user=user) == {
        'query': {
            'uri': 'http://bla.test',
            'some_field': 'something',
        },
        'offset': 3,
        'limit': 100,
        'user': user,
    }

def test_bad_search_parameters():
    request_params = {
        'offset': '3foo',
        'limit': '\' drop table annotations',
    }
    user = object()
    assert api._search_params(request_params, user=user) == {
        'query': {},
        'user': user,
    }

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
@patch('h.api.Annotation', new_callable=DictMock)
def test_create(mock_Annotation, mock_get_user):
    user = mock_get_user.return_value = MagicMock()
    user.id = 'alice'
    user.consumer.key = 'real_consumer'
    context = DummyResource()
    request = DummyRequest(json_body=_json_annotation)
    request.registry = MagicMock()

    result = api.create(context, request)

    annotation = mock_Annotation.instances[0]
    assert annotation['text'] == 'blabla'
    assert annotation['quote'] == 'blub'
    assert annotation['user'] == 'alice'
    assert annotation['consumer'] == 'real_consumer'
    assert annotation['permissions'] == _json_annotation['permissions']
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
    annotation = DictMock()(_old_annotation)
    context = annotation
    request = DummyRequest(json_body=_json_annotation)
    request.registry = MagicMock()
    request.has_permission = MagicMock(return_value=True)

    result = api.update(context, request)

    assert annotation['text'] == 'blabla'
    assert annotation['quote'] == 'blub'
    assert annotation['user'] == 'alice'
    assert annotation['consumer'] == 'real_consumer'
    assert annotation['permissions'] == _json_annotation['permissions']
    annotation.save.assert_called_once()
    assert request.registry.notify.call_count == 1, "Annotation event should have occured"
    assert request.registry.notify.call_args[0][0].action == 'update', "Annotation event action should be 'update'"
    assert result == context, "Annotation should have been returned"


@patch('h.api._anonymize_deletes')
def test_update_anonymize_deletes(mock_anonymize_deletes):
    annotation = DictMock()(_old_annotation)
    annotation['deleted'] = True
    context = annotation
    request = DummyRequest(json_body=_json_annotation)

    result = api.update(context, request)

    mock_anonymize_deletes.assert_called_once_with(annotation)


def test_anonymize_deletes():
    annotation = DictMock()(_old_annotation)
    annotation['deleted'] = True

    result = api._anonymize_deletes(annotation)

    assert 'user' not in annotation
    assert annotation['permissions'] == {
        'admin': [],
        'update': ['bob'],
        'read': ['group:__world__'],
        'delete': [],
    }


@patch('h.api._api_error')
def test_update_change_permissions_disallowed(mock_api_error):
    response_info = mock_api_error.return_value = MagicMock()
    annotation = DictMock()(_old_annotation)
    context = annotation
    request = DummyRequest(json_body=_json_annotation)
    request.registry = MagicMock()
    request.has_permission = MagicMock(return_value=False)

    result = api.update(context, request)

    assert mock_api_error.called
    assert annotation['text'] == 'old_text'
    assert annotation.save.call_count == 0
    assert request.registry.notify.call_count == 0, "Annotation event should NOT have occured"
    assert result == response_info, "Error information should have been returned"


def test_delete():
    annotation = DictMock()(_old_annotation)
    context = annotation
    request = DummyRequest()
    request.registry = MagicMock()

    result = api.delete(context, request)

    assert annotation.delete.assert_called_once()
    assert request.registry.notify.call_count == 1, "Annotation event should have occured"
    assert request.registry.notify.call_args[0][0].action == 'delete', "Annotation event action should be 'delete'"
    assert result == {'id': '1234', 'deleted': True}, "Deletion confirmation should have been returned"


_json_annotation = {
    'text':'blabla',
    'quote': 'blub',
    'created': '2040-05-20',
    'updated': '2040-05-23',
    'user': 'eve',
    'consumer': 'fake_consumer',
    'id': '1337',
    'permissions': {
        'admin': ['alice'],
        'update': ['alice'],
        'read': ['alice', 'group:__world__'],
        'delete': ['alice'],
    },
}

_old_annotation = {
    'text': 'old_text',
    'quote': 'old_quote',
    'created': '2010-01-01',
    'updated': '2010-01-02',
    'user': 'alice',
    'consumer': 'real_consumer',
    'id': '1234',
    'permissions': {
        'admin': ['alice'],
        'update': ['alice', 'bob'],
        'read': ['alice', 'group:__world__'],
        'delete': ['alice'],
    },
}
