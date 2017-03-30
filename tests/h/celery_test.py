# -*- coding: utf-8 -*-

import logging

import mock
import pytest

from billiard.einfo import ExceptionInfo

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

    def test_nipsa_cache(self, pyramid_config, pyramid_request):
        sender = mock.Mock(app=mock.Mock(request=pyramid_request))
        nipsa_svc = mock.Mock()
        pyramid_config.register_service(nipsa_svc, name='nipsa')

        celery.reset_nipsa_cache(sender)

        nipsa_svc.clear.assert_called_once_with()

    def test_transaction_commit_commits_request_transaction(self):
        sender = mock.Mock(spec=['app'])

        celery.transaction_commit(sender)

        sender.app.request.tm.commit.assert_called_once_with()

    def test_transaction_abort_aborts_request_transaction(self):
        sender = mock.Mock(spec=['app'])

        celery.transaction_abort(sender)

        sender.app.request.tm.abort.assert_called_once_with()

    def test_report_failure_reports_failure_in_debug_mode(self, patch):
        log = patch('h.celery.log')
        sender = mock.Mock(spec=['app'])
        sender.name = 'wibble'
        sender.app.request.debug = True

        # Make a fake ExceptionInfo object
        try:
            raise RuntimeError('asplode!')
        except:
            einfo = ExceptionInfo()

        celery.report_failure(sender, 'abc123', (), {}, einfo)

        assert log.error.called

    def test_report_failure_skipped_when_not_in_debug_mode(self, patch):
        log = patch('h.celery.log')
        sender = mock.Mock(spec=['app'])
        sender.name = 'wibble'
        sender.app.request.debug = False

        # Make a fake ExceptionInfo object
        try:
            raise RuntimeError('asplode!')
        except:
            einfo = ExceptionInfo()

        celery.report_failure(sender, 'abc123', (), {}, einfo)

        assert not log.error.called


def _patch(modulepath, request):
    patcher = mock.patch(modulepath, autospec=True)
    module = patcher.start()
    request.addfinalizer(patcher.stop)
    return module
