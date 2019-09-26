from __future__ import unicode_literals

from unittest import mock

from pyramid_retry import BeforeRetry
import pytest

from h.sentry.subscribers import add_retryable_error_to_sentry_context


class TestAddRetryableErrorToSentryContext:
    def test_it_adds_the_retryable_error_to_the_sentry_context(
        self, event, matchers, scope
    ):
        add_retryable_error_to_sentry_context(event)

        assert scope.set_extra.call_args_list == [
            mock.call(
                "Exception from attempt 1/3", "RuntimeError('Something went wrong',)"
            ),
            mock.call(
                "End of traceback from attempt 1/3",
                matchers.Regex(
                    r"^Traceback \(most recent call last\):\n"
                    r'  File "/.*/tests/h/sentry/subscribers_test\.py", line \d\d, in exception\n'
                    r'    raise RuntimeError\("Something went wrong"\)\n'
                    r"RuntimeError: Something went wrong\n$"
                ),
            ),
        ]

    def test_it_truncates_long_tracebacks(self, event, scope, traceback):
        traceback.format_exception.return_value = ["a" * 300 + "\n", "b" * 300 + "\n"]

        add_retryable_error_to_sentry_context(event)

        traceback_str = scope.set_extra.call_args[0][1]
        assert traceback_str.startswith("...aaa")
        assert traceback_str.endswith("bbb\n")
        assert len(traceback_str) == 512

    def test_it_doesnt_crash_if_theres_no_retry_environ(self, event):
        # I don't think this ever happens (as long as you have pyramid_retry
        # installed) but lets be defensive and make sure it doesn't crash if
        # retry.attempt or retry.attempts is missing from the environ.
        del event.environ["retry.attempt"]
        del event.environ["retry.attempts"]

        add_retryable_error_to_sentry_context(event)

    def test_it_doesnt_crash_if_theres_no_exception(self, event):
        # I don't think this ever happens in our app because we have an
        # exception view for Exception, but if an app raises a retryable
        # exception that isn't handled by an exception view then pyramid_retry
        # calls IBeforeRetry subscribers with request.exception = None.
        # Let's be defensive and make sure it doesn't crash if that happens.
        event.request.exception = None

        add_retryable_error_to_sentry_context(event)

    @pytest.fixture
    def event(self, pyramid_request):
        return BeforeRetry(pyramid_request)

    @pytest.fixture(autouse=True)
    def exception(self, pyramid_request):
        # Add an exception to request.exception as would happen with a real
        # pyramid_retry retry. Do this with a try/except in order to create an
        # exception object with an actual traceback.
        try:
            raise RuntimeError("Something went wrong")
        except RuntimeError as err:
            pyramid_request.exception = err

        return pyramid_request.exception

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        # Add information about retry attempts to request.environ as pyramid_retry does.
        pyramid_request.environ["retry.attempt"] = 0
        pyramid_request.environ["retry.attempts"] = 3
        return pyramid_request

    @pytest.fixture
    def scope(self, sentry_sdk):
        return sentry_sdk.configure_scope.return_value.__enter__.return_value

    @pytest.fixture(autouse=True)
    def sentry_sdk(self, patch):
        return patch("h.sentry.subscribers.sentry_sdk")

    @pytest.fixture
    def traceback(self, patch):
        return patch("h.sentry.subscribers.traceback")
