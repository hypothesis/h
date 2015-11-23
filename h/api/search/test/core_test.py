import mock
import pytest

from h.api.search import core


search_fixtures = pytest.mark.usefixtures('query', 'nipsa', 'models', 'log')


@search_fixtures
def test_search_passes_private_to_AuthFilter(query):
    request = mock.Mock()

    core.search(request, mock.Mock(), private=True)

    assert query.AuthFilter.call_args_list == [
        mock.call(request, private=True), mock.call(request, private=True)]


@search_fixtures
def test_search_queries_for_replies(query, models):
    """It should do a second query for replies to the results of the first."""
    # Mock the Builder objects that Builder() returns.
    builder = mock.Mock()
    query.Builder.side_effect = [
        mock.Mock(),  # We don't care about the first Builder in this test.
        builder
    ]

    # Mock the search results that search_raw() returns.
    models.Annotation.search_raw.side_effect = [
        # The first time search_raw() is called it returns the result of
        # querying for the top-level annotations only.
        {
            'hits': {
                'total': 3,
                'hits': [
                    {'_id': 'annotation_1', '_source': 'source'},
                    {'_id': 'annotation_2', '_source': 'source'},
                    {'_id': 'annotation_3', '_source': 'source'}
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

    core.search(mock.Mock(), mock.Mock())

    # It should construct a RepliesMatcher for replies to the annotations from
    # the first search.
    query.RepliesMatcher.assert_called_once_with(
        ['annotation_1', 'annotation_2', 'annotation_3'])

    # It should append the RepliesMatcher to the query builder.
    assert builder.append_matcher.call_args_list[-1] == mock.call(
        query.RepliesMatcher.return_value)

    # It should call search_raw() a second time with the body from the
    # query builder.
    assert models.Annotation.search_raw.call_count == 2
    last_call = models.Annotation.search_raw.call_args_list[-1]
    first_arg = last_call[0][0]
    assert first_arg == builder.build.return_value


@search_fixtures
def test_search_returns_replies(models):
    """It should return an Annotation for each reply from search_raw()."""
    models.Annotation.search_raw.side_effect = [
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
    models.Annotation.side_effect = [
        mock.sentinel.parent_annotation_object,
        mock.sentinel.reply_annotation_object_1,
        mock.sentinel.reply_annotation_object_2,
        mock.sentinel.reply_annotation_object_3,
    ]

    result = core.search(mock.Mock(), mock.Mock())

    assert result['replies'] == [
        mock.sentinel.reply_annotation_object_1,
        mock.sentinel.reply_annotation_object_2,
        mock.sentinel.reply_annotation_object_3
    ]


@search_fixtures
def test_search_logs_a_warning_if_there_are_too_many_replies(models, log):
    """It should log a warning if there's more than one page of replies."""
    models.Annotation.search_raw.side_effect = [
        {
            'hits': {
                'total': 3,
                'hits': [
                    {'_id': 'annotation_{n}'.format(n=n), '_source': 'source'}
                    for n in range(0, 3)]
            }
        },
        # The second call to search_raw() returns 'total': 11000 but only
        # returns the first 100 of 11000 hits.
        {
            'hits': {
                'total': 11000,
                'hits': [
                    {'_id': 'reply_{n}'.format(n=n), '_source': 'source'}
                    for n in range(0, 100)]
            }
        },
    ]

    core.search(mock.Mock(), mock.Mock())

    assert log.warn.call_count == 1


@search_fixtures
def test_search_does_not_log_a_warning_if_there_are_not_too_many_replies(
        models, log):
    """It should not log a warning if there's less than one page of replies."""
    models.Annotation.search_raw.side_effect = [
        {
            'hits': {
                'total': 3,
                'hits': [
                    {'_id': 'annotation_{n}'.format(n=n), '_source': 'source'}
                    for n in range(0, 3)]
            }
        },
        # The second call to search_raw() returns 'total': 100 and returns all
        # 100 hits in the first page pf results.
        {
            'hits': {
                'total': 100,
                'hits': [
                    {'_id': 'reply_{n}'.format(n=n), '_source': 'source'}
                    for n in range(0, 100)]
            }
        },
    ]

    core.search(mock.Mock(), mock.Mock())

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
def models(request):
    patcher = mock.patch('h.api.search.core.models', autospec=True)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result


@pytest.fixture
def log(request):
    patcher = mock.patch('h.api.search.core.log', autospec=True)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result
