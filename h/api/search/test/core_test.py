import mock
import pytest

from pyramid.testing import DummyRequest

from h.api.search import core


def dummy_search_results(start=1, count=0, name='annotation'):
    """Generate some dummy search results."""
    out = {'hits': {'total': 0, 'hits': []}}

    for i in range(start, start + count):
        out['hits']['total'] += 1
        out['hits']['hits'].append({
            '_id': 'id_{}'.format(i),
            '_source': {'name': '{}_{}'.format(name, i)},
        })

    return out


def dummy_request():
    """Return a mock request with a faked out Elasticsearch connection."""
    es = mock.Mock(spec_set=['conn', 'index', 't'])
    es.conn.search.return_value = dummy_search_results(0)

    return DummyRequest(es=es)


search_fixtures = pytest.mark.usefixtures('query', 'nipsa', 'log')


@search_fixtures
def test_search_passes_private_to_AuthFilter(query):
    request = dummy_request()

    core.search(request, {}, private=True)

    query.AuthFilter.assert_called_once_with(request, private=True)


@search_fixtures
def test_search_does_not_exclude_replies(query):
    request = dummy_request()

    result = core.search(request, {})

    assert not query.TopLevelAnnotationsFilter.called, (
        "Replies should not be filtered out of the 'rows' list if "
        "separate_replies=True is not given")
    assert 'replies' not in result, (
        "The separate 'replies' list should not be included in the result if "
        "separate_replies=True is not given")


@search_fixtures
def test_search_queries_for_replies(query):
    """It should do a second query for replies to the results of the first."""
    request = dummy_request()

    # Mock the Builder objects that Builder() returns.
    builder = mock.Mock()
    query.Builder.side_effect = [
        mock.Mock(),  # We don't care about the first Builder in this test.
        builder
    ]

    # Mock the search results.
    request.es.conn.search.side_effect = [
        # The first time search() is called it returns the result of querying
        # for the top-level annotations only.
        dummy_search_results(count=3),
        # The second call returns the result of querying for all the replies to
        # those annotations
        dummy_search_results(start=4, count=3, name='reply'),
    ]

    core.search(request, {}, separate_replies=True)

    # It should construct a RepliesMatcher for replies to the annotations from
    # the first search.
    query.RepliesMatcher.assert_called_once_with(['id_1', 'id_2', 'id_3'])

    # It should append the RepliesMatcher to the query builder.
    builder.append_matcher.assert_called_with(query.RepliesMatcher.return_value)

    # It should call search() a second time with the body from the
    # query builder.
    assert request.es.conn.search.call_count == 2
    _, last_call_kwargs = request.es.conn.search.call_args_list[-1]
    assert last_call_kwargs['body'] == builder.build.return_value


@search_fixtures
def test_search_returns_replies():
    """It should return an annotation dict for each reply from search()."""
    request = dummy_request()
    request.es.conn.search.side_effect = [
        # The first time search() is called it returns the result of querying
        # for the top-level annotations only.
        dummy_search_results(count=1),
        # The second call returns the result of querying for all the replies to
        # those annotations
        dummy_search_results(start=2, count=3, name='reply'),
    ]

    result = core.search(request, {}, separate_replies=True)

    assert result['replies'] == [
        {'name': 'reply_2', 'id': 'id_2'},
        {'name': 'reply_3', 'id': 'id_3'},
        {'name': 'reply_4', 'id': 'id_4'},
    ]


@search_fixtures
def test_search_logs_a_warning_if_there_are_too_many_replies(log):
    """It should log a warning if there's more than one page of replies."""
    request = dummy_request()
    parent_results = dummy_search_results(count=3)
    replies_results = dummy_search_results(count=100, name='reply')
    # The second call to search() returns 'total': 11000 but only returns
    # the first 100 of 11000 hits.
    replies_results['hits']['total'] = 11000
    request.es.conn.search.side_effect = [parent_results, replies_results]

    core.search(request, {}, separate_replies=True)

    assert log.warn.call_count == 1


@search_fixtures
def test_search_does_not_log_a_warning_if_there_are_not_too_many_replies(log):
    """It should not log a warning if there's less than one page of replies."""
    request = dummy_request()
    request.es.conn.search.side_effect = [
        dummy_search_results(count=3),
        dummy_search_results(count=100, start=4, name='reply'),
    ]

    core.search(request, {}, separate_replies=True)

    assert not log.warn.called


@pytest.fixture
def query(request):
    patcher = mock.patch('h.api.search.core.query', autospec=True)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result


@pytest.fixture
def nipsa(request):
    patcher = mock.patch('h.api.search.core.nipsa', autospec=True)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result


@pytest.fixture
def log(request):
    patcher = mock.patch('h.api.search.core.log', autospec=True)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result
