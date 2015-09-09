# -*- coding: utf-8 -*-

import mock
from webob import multidict

from h.api.search import core


@mock.patch("annotator.annotation.Annotation.search_raw")
@mock.patch("h.api.search.query.build")
def test_search_with_user_object(_, search_raw):
    """If search() gets a user arg it passes it to search_raw().

    Note: This test is testing the function's user param. You can also
    pass one or more user arguments in the request.params, those are
    tested elsewhere.

    """
    user = mock.MagicMock()

    core.search(request_params=multidict.NestedMultiDict(), user=user)

    first_call = search_raw.call_args_list[0]
    assert first_call[1]["user"] == user


@mock.patch("annotator.annotation.Annotation.search_raw")
@mock.patch("h.api.search.query.build")
def test_search_does_not_pass_userid_to_build(build, _):
    core.search(multidict.NestedMultiDict())
    assert build.call_args[1]["userid"] is None


@mock.patch("annotator.annotation.Annotation.search_raw")
@mock.patch("h.api.search.query.build")
def test_search_does_pass_userid_to_build(build, _):
    user = mock.Mock(id="test_id")

    core.search(multidict.NestedMultiDict(), user=user)

    assert build.call_args[1]["userid"] == "test_id"


@mock.patch("h.api.search.core.models.Annotation")
@mock.patch("h.api.search.core.query.build")
def test_search_queries_for_replies(_, Annotation):
    """It does a second Es query for replies to the results of the first."""
    ids = ['foo', 'bar', 'gar']
    Annotation.search_raw.side_effect = [
        # The first time search_raw() is called it returns the result of
        # querying for the top-level annotations only.
        {
            'hits': {
                'total': 3,
                'hits': [
                    {'_id': ids[0], '_source': 'source'},
                    {'_id': ids[1], '_source': 'source'},
                    {'_id': ids[2], '_source': 'source'}
                ]
            }
        },
        # The second call returns the result of querying for all the replies to
        # those annotations
        {
            'hits': {
                'total': 3,
                'hits': [
                    {'_id': 'reply_1', '_source': 'source'},
                    {'_id': 'reply_2', '_source': 'source'},
                    {'_id': 'reply_3', '_source': 'source'}
                ]
            }
        },
    ]
    user = mock.Mock()

    core.search(mock.Mock(), user=user)

    assert Annotation.search_raw.call_count == 2
    Annotation.search_raw.assert_called_with(
        {'query': {'terms': {'references': ids}}, 'size': 10000},
        user=user, raw_result=True)


@mock.patch("h.api.search.core.models.Annotation")
@mock.patch("h.api.search.core.query.build")
def test_search_returns_replies(_, Annotation):
    """It should return an Annotation for each reply from search_raw()."""
    Annotation.search_raw.side_effect = [
        # The first time search_raw() is called it returns the result of
        # querying for the top-level annotations only.
        {
            'hits': {
                'total': 1,
                'hits': [{'_id': 'parent_annotation_id', '_source': 'source'}]
            }
        },
        # The second call returns the result of querying for all the replies to
        # those annotations
        {
            'hits': {
                'total': 3,
                'hits': [
                    {'_id': 'reply_1', '_source': 'source'},
                    {'_id': 'reply_2', '_source': 'source'},
                    {'_id': 'reply_3', '_source': 'source'}
                ]
            }
        },
    ]
    # It should call Annotation() four times: first for the parent annotation
    # and then once for each reply.
    Annotation.side_effect = [
        mock.sentinel.parent_annotation_object,
        mock.sentinel.reply_annotation_object_1,
        mock.sentinel.reply_annotation_object_2,
        mock.sentinel.reply_annotation_object_3,
    ]

    result = core.search(mock.Mock())

    assert result['replies'] == [
        mock.sentinel.reply_annotation_object_1,
        mock.sentinel.reply_annotation_object_2,
        mock.sentinel.reply_annotation_object_3
    ]


@mock.patch("h.api.search.core.search")
def test_index_limit_is_20(search_func):
    """index() calls search with "limit": 20."""
    core.index()

    first_call = search_func.call_args_list[0]
    assert first_call[0][0]["limit"] == 20
