# -*- coding: utf-8 -*-

import pytest

import mock
from pyramid import httpexceptions

from h.views.activity import PAGE_SIZE
from h.views.activity import search


# The search view is just a skeleton at the moment, the only part we should
# test at the moment is that it returns a 404 response when the feature flag
# is turned off.
class TestSearch(object):
    def test_it_returns_404_when_feature_turned_off(self, pyramid_request):
        pyramid_request.feature.flags['search_page'] = False

        with pytest.raises(httpexceptions.HTTPNotFound):
            search(pyramid_request)

    def test_it_checks_for_redirects(self, pyramid_request, query):
        pyramid_request.feature.flags['search_page'] = True

        search(pyramid_request)

        query.check_url.assert_called_once_with(pyramid_request,
                                                query.extract.return_value)

    def test_it_executes_a_search_query(self, pyramid_request, query):
        pyramid_request.feature.flags['search_page'] = True

        search(pyramid_request)

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=PAGE_SIZE)

    def test_it_allows_to_specify_the_page_size(self, pyramid_request, query):
        pyramid_request.feature.flags['search_page'] = True

        pyramid_request.params['page_size'] = 100
        search(pyramid_request)

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=100)

    def test_it_uses_default_page_size_when_value_is_a_string(self, pyramid_request, query):
        pyramid_request.feature.flags['search_page'] = True

        pyramid_request.params['page_size'] = 'foobar'
        search(pyramid_request)

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=PAGE_SIZE)

    @pytest.mark.usefixtures('query')
    def test_is_uses_passed_in_page_size_for_pagination(self, pyramid_request, paginate):
        pyramid_request.feature.flags['search_page'] = True

        pyramid_request.params['page_size'] = 100
        search(pyramid_request)

        paginate.assert_called_once_with(pyramid_request,
                                         mock.ANY,
                                         page_size=100)

    @pytest.fixture
    def query(self, patch):
        return patch('h.views.activity.query')

    @pytest.fixture
    def paginate(self, patch):
        return patch('h.views.activity.paginate')
