# -*- coding: utf-8 -*-

import mock
from pyramid.request import Request
import pytest

from h import celery


def fake_bootstrap(config_uri, request=None):
    request.sentry = mock.sentinel.sentry
    return {
        'root': mock.sentinel.root
    }


class TestCelery(object):

    @pytest.fixture(autouse=True)
    def paster(self, request):
        paster = _patch('h.celery.paster', request)
        paster.bootstrap.side_effect = fake_bootstrap
        return paster

    def test_bootstrap_worker_calls_paster_bootstrap(self, paster):
        sender = mock.Mock(spec=['app'])

        celery.bootstrap_worker(sender)

        assert paster.bootstrap.call_count == 1

    def test_bootstrap_worker_attaches_request_to_app(self, paster):
        sender = mock.Mock(spec=['app'])

        celery.bootstrap_worker(sender)

        assert isinstance(sender.app.request, Request)

    def test_bootstrap_worker_sets_request_root(self, paster):
        sender = mock.Mock(spec=['app'])

        celery.bootstrap_worker(sender)

        assert sender.app.request.root == mock.sentinel.root


def _patch(modulepath, request):
    patcher = mock.patch(modulepath, autospec=True)
    module = patcher.start()
    request.addfinalizer(patcher.stop)
    return module
