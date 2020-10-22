from unittest import mock

from billiard.einfo import ExceptionInfo

from h import celery


class TestCelery:
    def test_bootstrap_worker_bootstraps_application(self):
        sender = mock.Mock(spec=["app"])

        celery.bootstrap_worker(sender)

        sender.app.webapp_bootstrap.assert_called_once_with()

    def test_bootstrap_worker_attaches_request_to_app(self):
        sender = mock.Mock(spec=["app"])
        request = sender.app.webapp_bootstrap.return_value

        celery.bootstrap_worker(sender)

        assert sender.app.request == request

    def test_nipsa_cache(self, pyramid_config, pyramid_request):
        sender = mock.Mock(app=mock.Mock(request=pyramid_request))
        nipsa_svc = mock.Mock()
        pyramid_config.register_service(nipsa_svc, name="nipsa")

        celery.reset_nipsa_cache(sender)

        nipsa_svc.clear.assert_called_once_with()

    def test_transaction_commit_commits_request_transaction(self):
        sender = mock.Mock(spec=["app"])

        celery.transaction_commit(sender)

        sender.app.request.tm.commit.assert_called_once_with()

    def test_transaction_abort_aborts_request_transaction(self):
        sender = mock.Mock(spec=["app"])

        celery.transaction_abort(sender)

        sender.app.request.tm.abort.assert_called_once_with()

    def test_report_failure_reports_failure_in_debug_mode(self, patch):
        log = patch("h.celery.log")
        sender = mock.Mock(spec=["app"])
        sender.name = "wibble"
        sender.app.request.debug = True

        # Make a fake ExceptionInfo object
        try:
            raise RuntimeError("asplode!")
        except RuntimeError:
            einfo = ExceptionInfo()

        celery.report_failure(sender, "abc123", (), {}, einfo)

        assert log.error.called

    def test_report_failure_skipped_when_not_in_debug_mode(self, patch):
        log = patch("h.celery.log")
        sender = mock.Mock(spec=["app"])
        sender.name = "wibble"
        sender.app.request.debug = False

        # Make a fake ExceptionInfo object
        try:
            raise RuntimeError("asplode!")
        except RuntimeError:
            einfo = ExceptionInfo()

        celery.report_failure(sender, "abc123", (), {}, einfo)

        assert not log.error.called
