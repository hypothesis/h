# -*- coding: utf-8 -*-

import mock
from webob import multidict
from pyramid import testing

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

    core.search(
        testing.DummyRequest(), request_params=multidict.NestedMultiDict(),
        user=user)

    first_call = search_raw.call_args_list[0]
    assert first_call[1]["user"] == user


@mock.patch("annotator.annotation.Annotation.search_raw")
@mock.patch("h.api.search.query.build")
def test_search_passes_request_to_build(build, _):
    request = mock.Mock()

    core.search(request, request.params, mock.Mock())

    assert build.call_args[0][0] == request


@mock.patch("h.api.search.core.search")
def test_index_limit_is_20(search_func):
    """index() calls search with "limit": 20."""
    core.index()

    first_call = search_func.call_args_list[0]
    assert first_call[0][0]["limit"] == 20
