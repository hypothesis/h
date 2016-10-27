# -*- coding: utf-8 -*-

import pytest

import mock
from pyramid import httpexceptions

from h.views import activity


@pytest.mark.usefixtures('paginate', 'query')
class TestSearch(object):
    def test_it_returns_404_when_feature_turned_off(self, pyramid_request):
        pyramid_request.feature.flags['search_page'] = False

        with pytest.raises(httpexceptions.HTTPNotFound):
            activity.search(pyramid_request)

    def test_it_checks_for_redirects(self, pyramid_request, query):
        activity.search(pyramid_request)

        query.check_url.assert_called_once_with(pyramid_request,
                                                query.extract.return_value)

    def test_it_executes_a_search_query(self, pyramid_request, query):
        activity.search(pyramid_request)

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=activity.PAGE_SIZE)

    def test_it_allows_to_specify_the_page_size(self, pyramid_request, query):
        pyramid_request.params['page_size'] = 100
        activity.search(pyramid_request)

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=100)

    def test_it_uses_default_page_size_when_value_is_a_string(self, pyramid_request, query):
        pyramid_request.params['page_size'] = 'foobar'
        activity.search(pyramid_request)

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=activity.PAGE_SIZE)

    def test_it_uses_passed_in_page_size_for_pagination(self, pyramid_request, paginate):
        pyramid_request.params['page_size'] = 100
        activity.search(pyramid_request)

        paginate.assert_called_once_with(pyramid_request,
                                         mock.ANY,
                                         page_size=100)

    def test_it_returns_usernames(self, pyramid_request, query):
        """
        It should return a list of usernames to the template.

        query.execute() returns userids, search() should replace these with
        just the username parts.

        """
        query.execute.return_value = mock.Mock(
            aggregations={
                'users': [
                    {'user': 'acct:test_user_1@hypothes.is'},
                    {'user': 'acct:test_user_2@hypothes.is'},
                    {'user': 'acct:test_user_3@hypothes.is'},
                ]
            }
        )

        result = activity.search(pyramid_request)

        assert result['aggregations']['users'] == [
            {'username': 'test_user_1'},
            {'username': 'test_user_2'},
            {'username': 'test_user_3'},
        ]

    def test_it_does_not_crash_if_there_are_no_users(self,
                                                     pyramid_request,
                                                     query):
        """
        It shouldn't crash if query.execute() returns no users.

        Sometimes there is no "users" key in the aggregations.

        """
        query.execute.return_value = mock.Mock(aggregations={})

        result = activity.search(pyramid_request)

        assert 'users' not in result['aggregations']

    @pytest.fixture
    def query(self, patch):
        return patch('h.views.activity.query')

    @pytest.fixture
    def paginate(self, patch):
        return patch('h.views.activity.paginate')

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.feature.flags['search_page'] = True
        return pyramid_request
