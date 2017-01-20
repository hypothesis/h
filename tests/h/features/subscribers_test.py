# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from pyramid.events import NewRequest

from h.features.subscribers import preload_flags


class TestPreloadFlags(object):
    def test_preloads_feature_flags(self, pyramid_request):
        event = NewRequest(pyramid_request)

        preload_flags(event)

        assert event.request.feature.loaded

    @pytest.mark.parametrize('path', [
        '/assets/some/style.css',
        '/_debug_toolbar/foo123',
    ])
    def test_does_not_preload_for_opted_out_requests(self, path, pyramid_request):
        pyramid_request.path = path
        event = NewRequest(pyramid_request)

        preload_flags(event)

        assert not event.request.feature.loaded
