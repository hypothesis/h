import mock
import pytest

from h.api.search import core

search_fixtures = pytest.mark.usefixtures('query', 'log')


@search_fixtures
def test_search_does_not_exclude_replies(query, pyramid_request):
    result = core.search(pyramid_request, {})

    assert not query.TopLevelAnnotationsFilter.called, (
        "Replies should not be filtered out of the 'rows' list if "
        "separate_replies=True is not given")
    assert 'replies' not in result, (
        "The separate 'replies' list should not be included in the result if "
        "separate_replies=True is not given")


@search_fixtures
def test_search_queries_for_replies(query, pyramid_request):
    """It should do a second query for replies to the results of the first."""
    # Mock the Builder objects that Builder() returns.
    builder = mock.Mock()
    query.Builder.side_effect = [
        mock.Mock(),  # We don't care about the first Builder in this test.
        builder
    ]

    # Mock the search results.
    pyramid_request.es.conn.search.side_effect = [
        # The first time search() is called it returns the result of querying
        # for the top-level annotations only.
        dummy_search_results(count=3),
        # The second call returns the result of querying for all the replies to
        # those annotations
        dummy_search_results(start=4, count=3, name='reply'),
    ]

    core.search(pyramid_request, {}, separate_replies=True)

    # It should construct a RepliesMatcher for replies to the annotations from
    # the first search.
    query.RepliesMatcher.assert_called_once_with(['id_1', 'id_2', 'id_3'])

    # It should append the RepliesMatcher to the query builder.
    builder.append_matcher.assert_called_with(query.RepliesMatcher.return_value)

    # It should call search() a second time with the body from the
    # query builder.
    assert pyramid_request.es.conn.search.call_count == 2
    _, last_call_kwargs = pyramid_request.es.conn.search.call_args_list[-1]
    assert last_call_kwargs['body'] == builder.build.return_value


@search_fixtures
def test_search_returns_replies(pyramid_request):
    """It should return an annotation dict for each reply from search()."""
    pyramid_request.es.conn.search.side_effect = [
        # The first time search() is called it returns the result of querying
        # for the top-level annotations only.
        dummy_search_results(count=1),
        # The second call returns the result of querying for all the replies to
        # those annotations
        dummy_search_results(start=2, count=3, name='reply'),
    ]

    result = core.search(pyramid_request, {}, separate_replies=True)

    assert result['replies'] == [
        {'name': 'reply_2', 'id': 'id_2'},
        {'name': 'reply_3', 'id': 'id_3'},
        {'name': 'reply_4', 'id': 'id_4'},
    ]


@search_fixtures
def test_search_logs_a_warning_if_there_are_too_many_replies(log, pyramid_request):
    """It should log a warning if there's more than one page of replies."""
    parent_results = dummy_search_results(count=3)
    replies_results = dummy_search_results(count=100, name='reply')
    # The second call to search() returns 'total': 11000 but only returns
    # the first 100 of 11000 hits.
    replies_results['hits']['total'] = 11000
    pyramid_request.es.conn.search.side_effect = [parent_results, replies_results]

    core.search(pyramid_request, {}, separate_replies=True)

    assert log.warn.call_count == 1


@search_fixtures
def test_search_does_not_log_a_warning_if_there_are_not_too_many_replies(log, pyramid_request):
    """It should not log a warning if there's less than one page of replies."""
    pyramid_request.es.conn.search.side_effect = [
        dummy_search_results(count=3),
        dummy_search_results(count=100, start=4, name='reply'),
    ]

    core.search(pyramid_request, {}, separate_replies=True)

    assert not log.warn.called


@pytest.mark.parametrize('private', [True, False])
def test_default_querybuilder_passes_private_to_AuthFilter(private, query, pyramid_request):
    core.default_querybuilder(pyramid_request, private=private)

    query.AuthFilter.assert_called_once_with(pyramid_request, private=private)


@pytest.mark.parametrize('filter_type', [
    'AuthFilter',
    'UriFilter',
    'GroupFilter'
])
def test_default_querybuilder_includes_default_filters(filter_type, matchers, pyramid_request):
    from h.api.search import query
    builder = core.default_querybuilder(pyramid_request)
    type_ = getattr(query, filter_type)

    assert matchers.instance_of(type_) in builder.filters


def test_default_querybuilder_includes_registered_filters(pyramid_request):
    filter_factory = mock.Mock(return_value=mock.sentinel.MY_FILTER,
                               spec_set=[])
    pyramid_request.registry[core.FILTERS_KEY] = [filter_factory]

    builder = core.default_querybuilder(pyramid_request)

    filter_factory.assert_called_once_with(pyramid_request)
    assert mock.sentinel.MY_FILTER in builder.filters


@pytest.mark.parametrize('matcher_type', [
    'AnyMatcher',
    'TagsMatcher',
])
def test_default_querybuilder_includes_default_matchers(matchers, matcher_type, pyramid_request):
    from h.api.search import query
    builder = core.default_querybuilder(pyramid_request)
    type_ = getattr(query, matcher_type)

    assert matchers.instance_of(type_) in builder.matchers


def test_default_querybuilder_includes_registered_matchers(pyramid_request):
    matcher_factory = mock.Mock(return_value=mock.sentinel.MY_MATCHER,
                                spec_set=[])
    pyramid_request.registry[core.MATCHERS_KEY] = [matcher_factory]

    builder = core.default_querybuilder(pyramid_request)

    matcher_factory.assert_called_once_with(pyramid_request)
    assert mock.sentinel.MY_MATCHER in builder.matchers


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


@pytest.fixture
def pyramid_request(pyramid_request):
    """Return a mock request with a faked out Elasticsearch connection."""
    pyramid_request.es = mock.Mock(spec_set=['conn', 'index', 't'])
    pyramid_request.es.conn.search.return_value = dummy_search_results(0)
    return pyramid_request


@pytest.fixture
def query(patch):
    return patch('h.api.search.core.query')


@pytest.fixture
def log(patch):
    return patch('h.api.search.core.log')
