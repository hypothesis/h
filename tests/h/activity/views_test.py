# -*- coding: utf-8 -*-

import pytest

from pyramid import httpexceptions

from h.activity import views


# The search view is just a skeleton at the moment, the only part we should
# test at the moment is that it returns a 404 response when the feature flag
# is turned off.
class TestSearch(object):
    def test_it_returns_404_when_feature_turned_off(self, pyramid_request):
        pyramid_request.feature.flags['activity_pages'] = False

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.search(pyramid_request)
