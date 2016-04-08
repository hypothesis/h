# -*- coding: utf-8 -*-

import logging

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

    @pytest.fixture(autouse=True)
    def register_signal(self, request):
        return _patch('h.celery.register_signal', request)

    @pytest.fixture(autouse=True)
    def register_logger_signal(self, request):
        return _patch('h.celery.register_logger_signal', request)

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

    def test_bootstrap_worker_configures_sentry_reporting(self,
                                                          register_signal,
                                                          register_logger_signal):
        sender = mock.Mock(spec=['app'])

        celery.bootstrap_worker(sender)

        register_signal.assert_called_once_with(mock.sentinel.sentry)
        register_logger_signal.assert_called_once_with(mock.sentinel.sentry,
                                                       loglevel=logging.ERROR)

    def test_reset_feature_flags_resets_request_feature_flags(self):
        sender = mock.Mock(spec=['app'])

        celery.reset_feature_flags(sender)

        sender.app.request.feature.clear.assert_called_once_with()

    def test_transaction_commit_commits_request_transaction(self):
        sender = mock.Mock(spec=['app'])

        celery.transaction_commit(sender)

        sender.app.request.tm.commit.assert_called_once_with()

    def test_transaction_abort_aborts_request_transaction(self):
        sender = mock.Mock(spec=['app'])

        celery.transaction_abort(sender)

        sender.app.request.tm.abort.assert_called_once_with()


def _patch(modulepath, request):
    patcher = mock.patch(modulepath, autospec=True)
    module = patcher.start()
    request.addfinalizer(patcher.stop)
    return module
