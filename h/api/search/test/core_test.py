# -*- coding: utf-8 -*-

import mock
import pytest
from webob import multidict
from pyramid import testing

from h.api.search import core


# The fixtures required to mock all of search()'s dependencies.
search_fixtures = pytest.mark.usefixtures('query', 'models')


@search_fixtures
def test_search_with_user_object(models):
    """If search() gets a user arg it passes it to search_raw().

    Note: This test is testing the function's user param. You can also
    pass one or more user arguments in the request.params, those are
    tested elsewhere.

    """
    user = mock.MagicMock()

    core.search(multidict.NestedMultiDict(), [], user=user)

    first_call = models.Annotation.search_raw.call_args_list[0]
    assert first_call[1]["user"] == user


@search_fixtures
def test_search_does_not_pass_userid_to_build(query):
    core.search(multidict.NestedMultiDict(), [])
    assert query.build.call_args[1]["userid"] is None


@search_fixtures
def test_search_does_pass_userid_to_build(query):
    user = mock.Mock(id="test_id")

    core.search(multidict.NestedMultiDict(), [], user=user)

    assert query.build.call_args[1]["userid"] == "test_id"


@mock.patch("annotator.annotation.Annotation.search_raw")
@mock.patch("h.api.search.query.build")
def test_search_passes_effective_principals_to_build(build, _):
    effective_principals = mock.Mock()

    core.search(mock.Mock(), effective_principals, user=mock.Mock())

    assert build.call_args[0][1] == effective_principals

@mock.patch("h.api.search.core.search")
def test_index_limit_is_20(search_func):
    """index() calls search with "limit": 20."""
    core.index([])

    first_call = search_func.call_args_list[0]
    assert first_call[0][0]["limit"] == 20


@pytest.fixture
def query(request):
    patcher = mock.patch('h.api.search.core.query', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def models(request):
    patcher = mock.patch('h.api.search.core.models', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
