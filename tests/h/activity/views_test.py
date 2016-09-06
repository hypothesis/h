# -*- coding: utf-8 -*-

import pytest

from pyramid import httpexceptions

from h.activity import views


# The search view is just a skeleton at the moment, the only part we should
# test at the moment is that it returns a 404 response when the feature flag
# is turned off.
class TestSearch(object):
    def test_it_returns_404_when_feature_turned_off(self, pyramid_request):
        pyramid_request.feature.flags['search_page'] = False

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.search(pyramid_request)

    def test_it_checks_for_redirects(self, pyramid_request, query):
        pyramid_request.feature.flags['search_page'] = True

        views.search(pyramid_request)

        query.check_url.assert_called_once_with(pyramid_request,
                                                query.extract.return_value)

    def test_it_executes_a_search_query(self, pyramid_request, query):
        pyramid_request.feature.flags['search_page'] = True

        views.search(pyramid_request)

        query.execute.assert_called_once_with(pyramid_request,
                                              query.extract.return_value,
                                              page_size=views.PAGE_SIZE)

    @pytest.fixture
    def query(self, patch):
        return patch('h.activity.views.query')
