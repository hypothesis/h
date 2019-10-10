import pytest
from unittest.mock import sentinel

from h_pyramid_sentry.filters.pyramid import is_retryable_error


class TestFilterRetryableError:
    TARGET_PACKAGE = "h_pyramid_sentry.filters.pyramid."

    def test_it_doesnt_filter_non_retryable_errors(self, Event):
        assert is_retryable_error(Event) is False

    def test_it_checks_whether_the_error_is_retryable(
        self, Event, is_error_retryable,
    ):
        is_retryable_error(Event)

        is_error_retryable.assert_called_once_with(
            sentinel.pyramid_request, Event.exception)

    def test_it_doesnt_filter_uncaught_errors(
        self, Event, get_current_request, is_error_retryable
    ):
        get_current_request.return_value = None

        assert is_retryable_error(Event) is False
        is_error_retryable.assert_not_called()

    def test_it_filters_retryable_errors(self, Event, is_error_retryable):
        is_error_retryable.return_value = True

        assert is_retryable_error(Event) is True

    @pytest.fixture(autouse=True)
    def get_current_request(self, patch):
        get_current_request = patch(self.TARGET_PACKAGE + "get_current_request")
        get_current_request.return_value = sentinel.pyramid_request
        return get_current_request

    @pytest.fixture(autouse=True)
    def is_error_retryable(self, patch):
        is_error_retryable = patch(
            self.TARGET_PACKAGE + "pyramid_retry.is_error_retryable")
        is_error_retryable.return_value = False
        return is_error_retryable
