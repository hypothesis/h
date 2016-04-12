# -*- coding: utf-8 -*-

import mock
from pyramid.testing import DummyRequest

from h.features import views


def test_features_status_returns_features(patch):
    feature_client = mock.Mock(spec_set=['all'])
    features = feature_client.all.return_value
    request = DummyRequest(feature=feature_client)

    result = views.features_status(request)

    assert result == features
