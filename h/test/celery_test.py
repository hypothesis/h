# -*- coding: utf-8 -*-

import logging

import mock
import pytest

from h import celery


class TestCelery(object):

    @pytest.fixture(autouse=True)
    def register_signal(self, request):
        return _patch('h.celery.register_signal', request)

    @pytest.fixture(autouse=True)
    def register_logger_signal(self, request):
        return _patch('h.celery.register_logger_signal', request)

    def test_bootstrap_worker_bootstraps_application(self):
        sender = mock.Mock(spec=['app'])

        celery.bootstrap_worker(sender)

        sender.app.webapp_bootstrap.assert_called_once_with()

    def test_bootstrap_worker_attaches_request_to_app(self):
        sender = mock.Mock(spec=['app'])
        request = sender.app.webapp_bootstrap.return_value

        celery.bootstrap_worker(sender)

        assert sender.app.request == request

    def test_bootstrap_worker_configures_sentry_reporting(self,
                                                          register_signal,
                                                          register_logger_signal):
        sender = mock.Mock(spec=['app'])
        request = sender.app.webapp_bootstrap.return_value
        request.sentry = mock.sentinel.sentry

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
