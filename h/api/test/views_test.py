# -*- coding: utf-8 -*-
# pylint: disable=protected-access

"""Defines unit tests for h.api.views."""

from mock import patch, MagicMock, Mock
import pytest
from pytest import fixture, raises
from pyramid.testing import DummyRequest, DummyResource

from .. import views


class DictMock(Mock):
    """A mock class providing basic dict semantics

    Usage example:
        Annotation = DictMock()
        a = Annotation({'text': 'bla'})
        a['user'] = 'alice'

        assert a['text'] == 'bla'
        assert a['user'] == 'alice'
    """
    def __init__(self, *args, **kwargs):
        super(DictMock, self).__init__(*args, **kwargs)
        self.instances = []
        def side_effect(*args_, **kwargs_):
            d = dict(*args_, **kwargs_)
            def getitem(name):
                return d[name]
            def setitem(name, value):
                d[name] = value
            def contains(name):
                return name in d
            m = Mock()
            m.__getitem__ = Mock(side_effect=getitem)
            m.__setitem__ = Mock(side_effect=setitem)
            m.__contains__ = Mock(side_effect=contains)
            m.get = Mock(side_effect=d.get)
            m.pop = Mock(side_effect=d.pop)
            m.update = Mock(side_effect=d.update)
            self.instances.append(m)
            return m
        self.side_effect = side_effect


@fixture()
def replace_io(monkeypatch):
    """For all tests, mock paths to the "outside" world"""
    monkeypatch.setattr(views, 'Annotation', DictMock())
    monkeypatch.setattr(views, '_publish_annotation_event', MagicMock())
    monkeypatch.setattr(views, '_api_error', MagicMock())
    nipsa = Mock(has_nipsa=Mock(return_value=False))
    monkeypatch.setattr(views, 'nipsa', nipsa)


@fixture()
def user(monkeypatch):
    """Provide a mock user"""
    user = MagicMock()
    user.id = 'alice'
    user.consumer.key = 'consumer_key'

    # Make auth.get_user() return our alice
    monkeypatch.setattr(views, 'get_user', lambda r: user)

    return user


@pytest.mark.usefixtures('replace_io')
def test_index():
    """Get the API descriptor"""

    result = views.index(DummyResource(), DummyRequest())

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


@patch('h.api.views._create_annotation')
@pytest.mark.usefixtures('replace_io')
def test_create(mock_create_annotation, user):
    request = DummyRequest(json_body=_new_annotation)

    annotation = views.create(request)

    views._create_annotation.assert_called_once_with(_new_annotation, user)
    assert annotation == views._create_annotation.return_value
    _assert_event_published('create')


@patch("h.api.views.Annotation.save")
@patch("h.api.views.nipsa.has_nipsa")
@patch("h.api.views.get_user")
def test_create_adds_nipsa_flag(get_user, has_nipsa, _):
    get_user.return_value = Mock(
        id="test_id", consumer=Mock(key="test_key"))
    has_nipsa.return_value = True
    request = DummyRequest(json_body=_new_annotation)

    annotation = views.create(request)

    assert annotation.get("nipsa") is True


@patch("h.api.views.Annotation.save")
@patch("h.api.views.nipsa.has_nipsa")
@patch("h.api.views.get_user")
def test_create_does_not_add_nipsa_flag(get_user, has_nipsa, _):
    get_user.return_value = Mock(
        id="test_id", consumer=Mock(key="test_key"))
    has_nipsa.return_value = False
    request = DummyRequest(json_body=_new_annotation)

    annotation = views.create(request)

    assert not annotation.get("nipsa")


@pytest.mark.usefixtures('replace_io')
def test_create_annotation(user):
    annotation = views._create_annotation(_new_annotation, user)
    assert annotation['text'] == 'blabla'
    assert annotation['user'] == 'alice'
    assert annotation['consumer'] == 'consumer_key'
    assert annotation['permissions'] == _new_annotation['permissions']
    annotation.save.assert_called_once()


@pytest.mark.usefixtures('replace_io')
def test_read():
    annotation = DummyResource()

    result = views.read(annotation, DummyRequest())

    _assert_event_published('read')
    assert result == annotation, "Annotation should have been returned"


@patch('h.api.views._update_annotation')
@pytest.mark.usefixtures('replace_io')
def test_update(mock_update_annotation):
    annotation = views.Annotation(_old_annotation)
    request = DummyRequest(json_body=_new_annotation)
    request.has_permission = MagicMock(return_value=True)

    result = views.update(annotation, request)

    views._update_annotation.assert_called_once_with(annotation,
                                                   _new_annotation,
                                                   True)
    _assert_event_published('update')
    assert result is annotation, "Annotation should have been returned"


@pytest.mark.usefixtures('replace_io')
def test_update_annotation(user):
    annotation = views.Annotation(_old_annotation)

    views._update_annotation(annotation, _new_annotation, True)

    assert annotation['text'] == 'blabla'
    assert annotation['quote'] == 'original_quote'
    assert annotation['user'] == 'alice'
    assert annotation['consumer'] == 'consumer_key'
    assert annotation['permissions'] == _new_annotation['permissions']
    annotation.save.assert_called_once()


@patch('h.api.views._anonymize_deletes')
@pytest.mark.usefixtures('replace_io')
def test_update_anonymize_deletes(mock_anonymize_deletes):
    annotation = views.Annotation(_old_annotation)
    annotation['deleted'] = True
    request = DummyRequest(json_body=_new_annotation)

    views.update(annotation, request)

    views._anonymize_deletes.assert_called_once_with(annotation)


@pytest.mark.usefixtures('replace_io')
def test_anonymize_deletes():
    annotation = views.Annotation(_old_annotation)
    annotation['deleted'] = True

    views._anonymize_deletes(annotation)

    assert 'user' not in annotation
    assert annotation['permissions'] == {
        'admin': [],
        'update': ['bob'],
        'read': ['group:__world__'],
        'delete': [],
    }


@pytest.mark.usefixtures('replace_io')
def test_update_change_permissions_disallowed():
    annotation = views.Annotation(_old_annotation)

    with raises(RuntimeError):
        views._update_annotation(annotation, _new_annotation, False)

    assert annotation['text'] == 'old_text'
    assert annotation.save.call_count == 0


@pytest.mark.usefixtures('replace_io')
def test_delete():
    annotation = views.Annotation(_old_annotation)

    result = views.delete(annotation, DummyRequest())

    assert annotation.delete.assert_called_once()
    _assert_event_published('delete')
    assert result == {'id': '1234', 'deleted': True}, "Deletion confirmation should have been returned"


def _assert_event_published(action):
    assert views._publish_annotation_event.call_count == 1
    assert views._publish_annotation_event.call_args[0][2] == action


_new_annotation = {
    'text': 'blabla',
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
    'quote': 'original_quote',
    'created': '2010-01-01',
    'updated': '2010-01-02',
    'user': 'alice',
    'consumer': 'consumer_key',
    'id': '1234',
    'permissions': {
        'admin': ['alice'],
        'update': ['alice', 'bob'],
        'read': ['alice', 'group:__world__'],
        'delete': ['alice'],
    },
}
