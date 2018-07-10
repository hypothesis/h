from __future__ import unicode_literals
import mock
import pytest

from h.search import core
from h.search.client import Client


class FakeStatsdClient(object):
    def pipeline(self):
        return FakeStatsdPipeline()


class FakeStatsdPipeline(object):
    def timer(self, name):
        return FakeStatsdTimer()

    def incr(self, name):
        pass

    def send(self):
        pass


class FakeStatsdTimer(object):
    def start(self):
        return self

    def stop(self):
        pass


class TestSearch(object):
    def test_run_searches_annotations(self, pyramid_request, _search_annotations):
        params = mock.Mock()

        _search_annotations.return_value = (0, [], {})

        search = core.Search(pyramid_request)
        search.run(params)

        _search_annotations.assert_called_once_with(search, params)

    def test_run_searches_replies(self,
                                  pyramid_request,
                                  _search_replies,
                                  _search_annotations):
        annotation_ids = [mock.Mock(), mock.Mock()]
        _search_annotations.return_value = (2, annotation_ids, {})

        search = core.Search(pyramid_request)
        search.run({})

        _search_replies.assert_called_once_with(search, annotation_ids)

    def test_run_returns_search_results(self,
                                        pyramid_request,
                                        _search_annotations,
                                        _search_replies):
        total = 4
        annotation_ids = ['id-1', 'id-3', 'id-6', 'id-5']
        reply_ids = ['reply-8', 'reply-5']
        aggregations = {'foo': 'bar'}
        _search_annotations.return_value = (total, annotation_ids, aggregations)
        _search_replies.return_value = reply_ids

        search = core.Search(pyramid_request)
        result = search.run({})

        assert result == core.SearchResult(total, annotation_ids, reply_ids, aggregations)

    def test_search_annotations_includes_replies_by_default(self, pyramid_request, query):
        search = core.Search(pyramid_request)
        search._search_annotations({})

        assert not query.TopLevelAnnotationsFilter.called, (
                "Replies should not be filtered out of the 'rows' list if "
                "separate_replies=True is not given")

    def test_search_annotations_parses_aggregation_results(self, pyramid_request):
        search = core.Search(pyramid_request)
        search.es.conn.search.return_value = {
            'hits': {
                'total': 0,
                'hits': [],
            },
            'aggregations': {
                'foobar': {'foo': 'bar'},
                'bazqux': {'baz': 'qux'},
            }
        }
        foobaragg = mock.Mock(key='foobar')
        bazquxagg = mock.Mock(key='bazqux')
        search.append_aggregation(foobaragg)
        search.append_aggregation(bazquxagg)

        search._search_annotations({})

        foobaragg.parse_result.assert_called_with({'foo': 'bar'})
        bazquxagg.parse_result.assert_called_with({'baz': 'qux'})

    def test_search_annotations_returns_parsed_aggregations(self, pyramid_request):
        search = core.Search(pyramid_request)
        search.es.conn.search.return_value = {
            'hits': {'total': 0, 'hits': []},
            'aggregations': {'foobar': {'foo': 'bar'}}
        }
        foobaragg = mock.Mock(key='foobar')
        search.append_aggregation(foobaragg)

        _, _, aggregations = search._search_annotations({})
        assert aggregations == {'foobar': foobaragg.parse_result.return_value}

    def test_search_annotations_works_with_stats_client(self, pyramid_request):
        search = core.Search(pyramid_request, stats=FakeStatsdClient())
        # This should not raise
        search._search_annotations({})

    def test_search_replies_skips_search_by_default(self, pyramid_request):
        search = core.Search(pyramid_request)
        search._search_replies(['id-1', 'id-2'])

        assert not search.es.conn.search.called

    def test_search_annotations_excludes_replies_when_asked(self, pyramid_request, query):
        search = core.Search(pyramid_request, separate_replies=True)

        search._search_annotations({})

        assert mock.call(query.TopLevelAnnotationsFilter()) in \
            search.builder.append_filter.call_args_list

    def test_search_replies_adds_a_replies_matcher(self, pyramid_request, query):
        search = core.Search(pyramid_request, separate_replies=True)

        search._search_replies(['id-1', 'id-2'])

        assert mock.call(query.RepliesMatcher(['id-1', 'id-2'])) in \
            search.reply_builder.append_matcher.call_args_list

    def test_search_replies_searches_replies_when_asked(self, pyramid_request):
        search = core.Search(pyramid_request, separate_replies=True)

        search.es.conn.search.return_value = {
            'hits': {
                'total': 2,
                'hits': [{'_id': 'reply-1'}, {'_id': 'reply-2'}],
            }
        }

        assert search._search_replies(['id-1']) == ['reply-1', 'reply-2']

    def test_search_replies_logs_warning_if_there_are_too_many_replies(self, pyramid_request, log):
        search = core.Search(pyramid_request, separate_replies=True)

        search.es.conn.search.return_value = {
            'hits': {
                'total': 1100,
                'hits': [{'_id': 'reply-1'}],
            }
        }

        search._search_replies(['id-1'])
        assert log.warn.call_count == 1

    def test_search_replies_works_with_stats_client(self, pyramid_request):
        search = core.Search(pyramid_request,
                             stats=FakeStatsdClient(),
                             separate_replies=True)
        # This should not raise
        search._search_replies(['id-1'])

    def test_append_filter_appends_to_annotation_builder(self, pyramid_request):
        filter_ = mock.Mock()
        search = core.Search(pyramid_request)
        search.builder = mock.Mock()

        search.append_filter(filter_)

        search.builder.append_filter.assert_called_once_with(filter_)

    def test_append_filter_appends_to_reply_builder(self, pyramid_request):
        filter_ = mock.Mock()
        search = core.Search(pyramid_request)
        search.reply_builder = mock.Mock()

        search.append_filter(filter_)

        search.reply_builder.append_filter.assert_called_once_with(filter_)

    def test_append_matcher_appends_to_annotation_builder(self, pyramid_request):
        matcher = mock.Mock()

        search = core.Search(pyramid_request)
        search.builder = mock.Mock()
        search.append_matcher(matcher)

        search.builder.append_matcher.assert_called_once_with(matcher)

    def test_append_matcher_appends_to_reply_builder(self, pyramid_request):
        matcher = mock.Mock()
        search = core.Search(pyramid_request)
        search.reply_builder = mock.Mock()

        search.append_matcher(matcher)

        search.reply_builder.append_matcher.assert_called_once_with(matcher)

    def test_append_aggregation_appends_to_annotation_builder(self, pyramid_request):
        aggregation = mock.Mock()
        search = core.Search(pyramid_request)
        search.builder = mock.Mock()

        search.append_aggregation(aggregation)

        search.builder.append_aggregation.assert_called_once_with(aggregation)

    @pytest.fixture
    def _search_annotations(self, patch):
        return patch('h.search.core.Search._search_annotations')

    @pytest.fixture
    def _search_replies(self, patch):
        return patch('h.search.core.Search._search_replies')

    @pytest.fixture
    def query(self, patch):
        return patch('h.search.core.query')

    @pytest.fixture
    def log(self, patch):
        return patch('h.search.core.log')


# @search_fixtures
# def test_search_logs_a_warning_if_there_are_too_many_replies(log, pyramid_request):
#     """It should log a warning if there's more than one page of replies."""
#     parent_results = dummy_search_results(count=3)
#     replies_results = dummy_search_results(count=100, name='reply')
#     # The second call to search() returns 'total': 11000 but only returns
#     # the first 100 of 11000 hits.
#     replies_results['hits']['total'] = 11000
#     pyramid_request.es.conn.search.side_effect = [parent_results, replies_results]
#
#     core.search(pyramid_request, {}, separate_replies=True)
#
#     assert log.warn.call_count == 1


# @search_fixtures
# def test_search_does_not_log_a_warning_if_there_are_not_too_many_replies(log, pyramid_request):
#     """It should not log a warning if there's less than one page of replies."""
#     pyramid_request.es.conn.search.side_effect = [
#         dummy_search_results(count=3),
#         dummy_search_results(count=100, start=4, name='reply'),
#     ]
#
#     core.search(pyramid_request, {}, separate_replies=True)
#
#     assert not log.warn.called


@pytest.mark.parametrize('filter_type', [
    'DeletedFilter',
    'AuthFilter',
    'UriFilter',
    'UserFilter',
    'GroupFilter',
])
def test_default_querybuilder_includes_default_filters(filter_type, matchers, pyramid_request):
    from h.search import query
    builder = core.Search._default_querybuilder(pyramid_request)
    type_ = getattr(query, filter_type)

    assert matchers.InstanceOf(type_) in builder.filters


@pytest.mark.parametrize('matcher_type', [
    'AnyMatcher',
    'TagsMatcher',
])
def test_default_querybuilder_includes_default_matchers(matchers, matcher_type, pyramid_request):
    from h.search import query
    builder = core.Search._default_querybuilder(pyramid_request)
    type_ = getattr(query, matcher_type)

    assert matchers.InstanceOf(type_) in builder.matchers


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
    pyramid_request.es = mock.create_autospec(Client, spec_set=True, instance=True)
    pyramid_request.es.mapping_type = "annotation"
    pyramid_request.es.conn.search.return_value = dummy_search_results(0)
    return pyramid_request


@pytest.fixture
def log(patch):
    return patch('h.search.core.log')
