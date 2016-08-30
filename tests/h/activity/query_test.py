# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from pyramid.httpexceptions import HTTPFound
from webob.multidict import MultiDict

from h.activity.query import (
    extract,
    check_url,
)


class TestExtract(object):
    def test_parses_param_value_with_parser(self, parse, pyramid_request):
        pyramid_request.GET['q'] = 'giraffe'

        extract(pyramid_request, parse=parse)

        parse.assert_called_once_with('giraffe')

    def test_returns_empty_results_when_q_param_is_missing(self, parse, pyramid_request):
        result = extract(pyramid_request, parse=parse)
        assert result == parse.return_value

    def test_returns_parse_results(self, parse, pyramid_request):
        parse.return_value = {'foo': 'bar'}
        pyramid_request.GET['q'] = 'giraffe'

        result = extract(pyramid_request, parse=parse)

        assert result == {'foo': 'bar'}

    def test_overrides_group_term_for_group_search_requests(self, parse, pyramid_request):
        """
        If the query sent to a group search page includes a group, we override
        it, because otherwise we'll display the union of the results for those
        two groups, which makes no sense.
        """
        parse.return_value = MultiDict({'foo': 'bar',
                                        'group': 'whattheusersent'})
        pyramid_request.matched_route.name = 'activity.group_search'
        pyramid_request.matchdict['pubid'] = 'abcd1234'
        pyramid_request.GET['q'] = 'giraffe'

        result = extract(pyramid_request, parse=parse)

        assert result.dict_of_lists() == {'foo': ['bar'],
                                          'group': ['abcd1234']}

    def test_overrides_user_term_for_user_search_requests(self, parse, pyramid_request):
        """
        If the query sent to a user search page includes a user, we override
        it, because otherwise we'll display the union of the results for those
        two users, which makes no sense.
        """
        parse.return_value = MultiDict({'foo': 'bar',
                                        'user': 'whattheusersent'})
        pyramid_request.matched_route.name = 'activity.user_search'
        pyramid_request.matchdict['username'] = 'josiah'
        pyramid_request.GET['q'] = 'giraffe'

        result = extract(pyramid_request, parse=parse)

        assert result.dict_of_lists() == {'foo': ['bar'],
                                          'user': ['josiah']}

    @pytest.fixture
    def parse(self):
        return mock.Mock(spec_set=[], return_value=MultiDict({'foo': 'bar'}))


@pytest.mark.usefixtures('routes')
class TestCheckURL(object):
    def test_redirects_to_group_search_page_if_one_group_in_query(self, pyramid_request, unparse):
        query = MultiDict({'group': 'abcd1234'})

        with pytest.raises(HTTPFound) as e:
            check_url(pyramid_request, query, unparse=unparse)

        assert e.value.location == '/act/groups/abcd1234?q=UNPARSED_QUERY'

    def test_removes_group_term_from_query(self, pyramid_request, unparse):
        query = MultiDict({'group': 'abcd1234'})

        with pytest.raises(HTTPFound):
            check_url(pyramid_request, query, unparse=unparse)

        unparse.assert_called_once_with({})

    def test_preserves_other_query_terms_for_group_search(self, pyramid_request, unparse):
        query = MultiDict({'group': 'abcd1234', 'tag': 'foo'})

        with pytest.raises(HTTPFound):
            check_url(pyramid_request, query, unparse=unparse)

        unparse.assert_called_once_with({'tag': 'foo'})

    def test_redirects_to_user_search_page_if_one_group_in_query(self, pyramid_request, unparse):
        query = MultiDict({'user': 'jose'})

        with pytest.raises(HTTPFound) as e:
            check_url(pyramid_request, query, unparse=unparse)

        assert e.value.location == '/act/users/jose?q=UNPARSED_QUERY'

    def test_removes_user_term_from_query(self, pyramid_request, unparse):
        query = MultiDict({'user': 'jose'})

        with pytest.raises(HTTPFound):
            check_url(pyramid_request, query, unparse=unparse)

        unparse.assert_called_once_with({})

    def test_preserves_other_query_terms_for_user_search(self, pyramid_request, unparse):
        query = MultiDict({'user': 'jose', 'tag': 'foo'})

        with pytest.raises(HTTPFound):
            check_url(pyramid_request, query, unparse=unparse)

        unparse.assert_called_once_with({'tag': 'foo'})

    def test_does_nothing_with_non_matching_queries(self, pyramid_request, unparse):
        query = MultiDict({'tag': 'foo'})

        result = check_url(pyramid_request, query, unparse=unparse)

        assert result is None

    def test_does_nothing_if_not_on_search_page(self, pyramid_request, unparse):
        pyramid_request.matched_route.name = 'activity.group_search'
        query = MultiDict({'group': 'abcd1234'})

        result = check_url(pyramid_request, query, unparse=unparse)

        assert result is None

    @pytest.fixture
    def unparse(self):
        return mock.Mock(spec_set=[], return_value='UNPARSED_QUERY')


@pytest.fixture
def pyramid_request(pyramid_request):
    class DummyRoute(object):
        name = 'activity.search'
    pyramid_request.matched_route = DummyRoute()
    return pyramid_request


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('activity.group_search', '/act/groups/{pubid}')
    pyramid_config.add_route('activity.user_search', '/act/users/{username}')
