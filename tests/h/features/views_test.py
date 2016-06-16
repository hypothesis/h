# -*- coding: utf-8 -*-

import mock

from h.features import views


def test_features_status_returns_features(patch, pyramid_request):
    feature_client = mock.Mock(spec_set=['all'])
    features = feature_client.all.return_value
    pyramid_request.feature = feature_client

    result = views.features_status(pyramid_request)

    assert result == features
