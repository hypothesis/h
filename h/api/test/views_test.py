# -*- coding: utf-8 -*-
# pylint: disable=protected-access

"""Defines unit tests for h.api.views."""

from mock import patch, MagicMock, Mock
from pytest import fixture, raises
from pyramid.testing import DummyRequest, DummyResource
import webob

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


@fixture()
def user(monkeypatch):
    """Provide a mock user"""
    user = MagicMock()
    user.id = 'alice'
    user.consumer.key = 'consumer_key'

    # Make auth.get_user() return our alice
    monkeypatch.setattr(views, 'get_user', lambda r: user)

    return user


def test_index(replace_io):
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
def test_create(mock_create_annotation, user, replace_io):
    request = DummyRequest(json_body=_new_annotation)

    annotation = views.create(request)

    views._create_annotation.assert_called_once_with(_new_annotation, user)
    assert annotation == views._create_annotation.return_value
    _assert_event_published('create')


def test_create_annotation(user, replace_io):
    annotation = views._create_annotation(_new_annotation, user)
    assert annotation['text'] == 'blabla'
    assert annotation['user'] == 'alice'
    assert annotation['consumer'] == 'consumer_key'
    assert annotation['permissions'] == _new_annotation['permissions']
    annotation.save.assert_called_once()


def test_read(replace_io):
    annotation = DummyResource()

    result = views.read(annotation, DummyRequest())

    _assert_event_published('read')
    assert result == annotation, "Annotation should have been returned"


@patch('h.api.views._update_annotation')
def test_update(mock_update_annotation, replace_io):
    annotation = views.Annotation(_old_annotation)
    request = DummyRequest(json_body=_new_annotation)
    request.has_permission = MagicMock(return_value=True)

    result = views.update(annotation, request)

    views._update_annotation.assert_called_once_with(annotation,
                                                   _new_annotation,
                                                   True)
    _assert_event_published('update')
    assert result is annotation, "Annotation should have been returned"


def test_update_annotation(user, replace_io):
    annotation = views.Annotation(_old_annotation)

    views._update_annotation(annotation, _new_annotation, True)

    assert annotation['text'] == 'blabla'
    assert annotation['quote'] == 'original_quote'
    assert annotation['user'] == 'alice'
    assert annotation['consumer'] == 'consumer_key'
    assert annotation['permissions'] == _new_annotation['permissions']
    annotation.save.assert_called_once()


@patch('h.api.views._anonymize_deletes')
def test_update_anonymize_deletes(mock_anonymize_deletes, replace_io):
    annotation = views.Annotation(_old_annotation)
    annotation['deleted'] = True
    request = DummyRequest(json_body=_new_annotation)

    views.update(annotation, request)

    views._anonymize_deletes.assert_called_once_with(annotation)


def test_anonymize_deletes(replace_io):
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


def test_update_change_permissions_disallowed(replace_io):
    annotation = views.Annotation(_old_annotation)

    with raises(RuntimeError):
        views._update_annotation(annotation, _new_annotation, False)

    assert annotation['text'] == 'old_text'
    assert annotation.save.call_count == 0


def test_delete(replace_io):
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


class TestSearch(object):
    # pylint: disable=no-self-use

    """Unit tests for the _search() function."""

    @patch("annotator.annotation.Annotation.search_raw")
    def test_offset_defaults_to_0(self, search_raw):
        """If no offset is given search_raw() is called with "from": 0."""
        views._search(request_params=webob.multidict.NestedMultiDict())

        first_call = search_raw.call_args_list[0]
        assert first_call[0][0]["from"] == 0

    @patch("annotator.annotation.Annotation.search_raw")
    def test_custom_offsets_are_passed_in(self, search_raw):
        """If an offset is given it's passed to search_raw() as "from"."""
        views._search(request_params=webob.multidict.NestedMultiDict({"offset": 7}))

        first_call = search_raw.call_args_list[0]
        assert first_call[0][0]["from"] == 7

    @patch("annotator.annotation.Annotation.search_raw")
    def test_offset_string_is_converted_to_int(self, search_raw):
        """'offset' arguments should be converted from strings to ints."""
        views._search(request_params={"offset": "23"})

        first_call = search_raw.call_args_list[0]
        assert first_call[0][0]["from"] == 23

    @patch("annotator.annotation.Annotation.search_raw")
    def test_invalid_offset(self, search_raw):
        """Invalid 'offset' params should be ignored."""
        for invalid_offset in ("foo", '', '   ', "-23", "32.7"):
            views._search(request_params={"offset": invalid_offset})

            first_call = search_raw.call_args_list[0]
            assert first_call[0][0]["from"] == 0

    @patch("annotator.annotation.Annotation.search_raw")
    def test_limit_defaults_to_20(self, search_raw):
        """If no limit is given search_raw() is called with "size": 20."""
        views._search(request_params=webob.multidict.NestedMultiDict())

        first_call = search_raw.call_args_list[0]
        assert first_call[0][0]["size"] == 20

    @patch("annotator.annotation.Annotation.search_raw")
    def test_custom_limits_are_passed_in(self, search_raw):
        """If a limit is given it's passed to search_raw() as "size"."""
        views._search(request_params=webob.multidict.NestedMultiDict({"limit": 7}))

        first_call = search_raw.call_args_list[0]
        assert first_call[0][0]["size"] == 7

    @patch("annotator.annotation.Annotation.search_raw")
    def test_limit_strings_are_converted_to_ints(self, search_raw):
        """String values for limit should be converted to ints."""
        views._search(request_params={"limit": "17"})

        first_call = search_raw.call_args_list[0]
        assert first_call[0][0]["size"] == 17

    @patch("annotator.annotation.Annotation.search_raw")
    def test_invalid_limit(self, search_raw):
        """Invalid 'limit' params should be ignored."""
        for invalid_limit in ("foo", '', '   ', "-23", "32.7"):
            views._search(request_params={"limit": invalid_limit})

            first_call = search_raw.call_args_list[0]
            assert first_call[0][0]["size"] == 20  # (20 is the default value.)

    @patch("annotator.annotation.Annotation.search_raw")
    def test_query_defaults_to_match_all(self, search_raw):
        """If no query is given search_raw is called with "match_all": {}."""
        views._search(request_params=webob.multidict.NestedMultiDict())

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {"bool": {"must": [{"match_all": {}}]}}

    @patch("annotator.annotation.Annotation.search_raw")
    def test_sort_is_by_updated(self, search_raw):
        """search_raw() is called with sort "updated"."""
        views._search(request_params=webob.multidict.NestedMultiDict())

        first_call = search_raw.call_args_list[0]
        sort = first_call[0][0]["sort"]
        assert len(sort) == 1
        assert sort[0].keys() == ["updated"]

    @patch("annotator.annotation.Annotation.search_raw")
    def test_sort_includes_ignore_unmapped(self, search_raw):
        """'ignore_unmapped': True is automatically passed to search_raw()."""
        views._search(request_params=webob.multidict.NestedMultiDict())

        first_call = search_raw.call_args_list[0]
        sort = first_call[0][0]["sort"]
        assert sort[0]["updated"]["ignore_unmapped"] == True

    @patch("annotator.annotation.Annotation.search_raw")
    def test_custom_sort(self, search_raw):
        """Custom sorts should be passed on to search_raw()."""
        views._search(
            request_params=webob.multidict.NestedMultiDict({"sort": "title"}))

        first_call = search_raw.call_args_list[0]

        sort = first_call[0][0]["sort"]
        assert sort == [{'title': {'ignore_unmapped': True, 'order': 'desc'}}]


    @patch("annotator.annotation.Annotation.search_raw")
    def test_order_defaults_to_desc(self, search_raw):
        """'order': "desc" is to search_raw()."""
        views._search(request_params=webob.multidict.NestedMultiDict())

        first_call = search_raw.call_args_list[0]
        sort = first_call[0][0]["sort"]
        assert sort[0]["updated"]["order"] == "desc"

    @patch("annotator.annotation.Annotation.search_raw")
    def test_custom_order(self, search_raw):
        """'order' params are passed to search_raw() if given."""
        views._search(
            request_params=webob.multidict.NestedMultiDict({"order": "asc"}))

        first_call = search_raw.call_args_list[0]

        sort = first_call[0][0]["sort"]
        assert sort[0]["updated"]["order"] == "asc"

    @patch("annotator.annotation.Annotation.search_raw")
    def test_search_for_user(self, search_raw):
        """'user' params are passed to search_raw() in the "match"."""
        views._search(
            request_params=webob.multidict.NestedMultiDict({"user": "bob"}))

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {"must": [{"match": {"user": "bob"}}]}}

    @patch("annotator.annotation.Annotation.search_raw")
    def test_search_for_multiple_users(self, search_raw):
        """Multiple "user" params go into multiple "match" dicts."""
        params = webob.multidict.MultiDict()
        params.add("user", "fred")
        params.add("user", "bob")

        views._search(request_params=params)

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {
                "must": [
                    {"match": {"user": "fred"}},
                    {"match": {"user": "bob"}}
                ]
            }
        }

    @patch("annotator.annotation.Annotation.search_raw")
    def test_search_for_tag(self, search_raw):
        """'tags' params are passed to search_raw() in the "match"."""
        views._search(
            request_params=webob.multidict.NestedMultiDict({"tags": "foo"}))

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {"must": [{"match": {"tags": "foo"}}]}}

    @patch("annotator.annotation.Annotation.search_raw")
    def test_search_for_multiple_tags(self, search_raw):
        """Multiple "tags" params go into multiple "match" dicts."""
        params = webob.multidict.MultiDict()
        params.add("tags", "foo")
        params.add("tags", "bar")

        views._search(request_params=params)

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {
                "must": [
                    {"match": {"tags": "foo"}},
                    {"match": {"tags": "bar"}}
                ]
            }
        }

    @patch("annotator.annotation.Annotation.search_raw")
    def test_combined_user_and_tag_search(self, search_raw):
        """A 'user' and a 'param' at the same time are handled correctly."""
        views._search(
            request_params=webob.multidict.NestedMultiDict(
                {"user": "bob", "tags": "foo"}))

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {"must": [
                {"match": {"user": "bob"}},
                {"match": {"tags": "foo"}},
            ]}}

    @patch("annotator.annotation.Annotation.search_raw")
    def test_keyword_search(self, search_raw):
        """Keywords are passed to search_raw() as a multi_match query."""
        params = webob.multidict.MultiDict()
        params.add("any", "howdy")

        views._search(request_params=params)

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "fields": ["quote", "tags", "text", "uri.parts",
                                       "user"],
                            "query": ["howdy"],
                            "type": "cross_fields"
                        }
                    }
                ]
            }
        }

    @patch("annotator.annotation.Annotation.search_raw")
    def test_multiple_keyword_search(self, search_raw):
        """Multiple keywords at once are handled correctly."""
        params = webob.multidict.MultiDict()
        params.add("any", "howdy")
        params.add("any", "there")

        views._search(request_params=params)

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {"must": [{"multi_match": {
                "fields": ["quote", "tags", "text", "uri.parts", "user"],
                "query": ["howdy", "there"],
                "type": "cross_fields"
            }}]}
        }

    @patch("annotator.annotation.Annotation.search_raw")
    def test_uri_search(self, search_raw):
        """_search() passes "uri" args on to search_raw() in the "match" dict.

        This is what happens when you open the sidebar on a page and it loads
        all the annotations of that page.

        """
        views._search(
            request_params=webob.multidict.NestedMultiDict(
                {"uri": "http://example.com/"}))

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {"must": [{"match": {"uri": "http://example.com/"}}]}}

    @patch("annotator.annotation.Annotation.search_raw")
    def test_single_text_param(self, search_raw):
        """_search() passes "text" params to search_raw() in a "match" dict."""
        views._search(
            request_params=webob.multidict.NestedMultiDict({"text": "foobar"}))

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {"must": [{"match": {"text": "foobar"}}]}}

    @patch("annotator.annotation.Annotation.search_raw")
    def test_multiple_text_params(self, search_raw):
        """Multiple "test" request params produce multiple "match" dicts."""
        params = webob.multidict.MultiDict()
        params.add("text", "foo")
        params.add("text", "bar")
        views._search(request_params=params)

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {
                "must": [
                    {"match": {"text": "foo"}},
                    {"match": {"text": "bar"}}
                ]
            }
        }

    @patch("annotator.annotation.Annotation.search_raw")
    def test_single_quote_param(self, search_raw):
        """_search() passes a "quote" param to search_raw() in a "match"."""
        views._search(
            request_params=webob.multidict.NestedMultiDict({"quote": "foobar"}))

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {"must": [{"match": {"quote": "foobar"}}]}}

    @patch("annotator.annotation.Annotation.search_raw")
    def test_multiple_quote_params(self, search_raw):
        """Multiple "quote" request params produce multiple "match" dicts."""
        params = webob.multidict.MultiDict()
        params.add("quote", "foo")
        params.add("quote", "bar")
        views._search(request_params=params)

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {
            "bool": {
                "must": [
                    {"match": {"quote": "foo"}},
                    {"match": {"quote": "bar"}}
                ]
            }
        }

    @patch("annotator.annotation.Annotation.search_raw")
    def test_user_object(self, search_raw):
        """If _search() gets a user arg it passes it to search_raw().

        Note: This test is testing the function's user param. You can also
        pass one or more user arguments in the request.params, those are
        tested elsewhere.

        """
        user = MagicMock()

        views._search(request_params=webob.multidict.NestedMultiDict(), user=user)

        first_call = search_raw.call_args_list[0]
        assert first_call[1]["user"] == user

    @patch("annotator.annotation.Annotation.search_raw")
    def test_with_evil_arguments(self, search_raw):
        params = webob.multidict.NestedMultiDict({
            "offset": "3foo",
            "limit": '\' drop table annotations'
        })

        views._search(request_params=params)

        first_call = search_raw.call_args_list[0]
        query = first_call[0][0]["query"]
        assert query == {'bool': {'must': [{'match_all': {}}]}}
