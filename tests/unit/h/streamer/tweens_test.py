from unittest import mock

import pytest

from h.streamer.tweens import close_db_session_tween_factory


class TestCloseTheDBSessionTweenFactory:
    def test_it_calls_the_handler(
        self, close_db_session_tween, handler, pyramid_request
    ):
        close_db_session_tween(pyramid_request)

        handler.assert_called_once_with(pyramid_request)

    def test_it_closes_the_db_session(self, close_db_session_tween, pyramid_request):
        close_db_session_tween(pyramid_request)

        pyramid_request.db.close.assert_called_once_with()

    def test_it_closes_the_db_session_if_an_exception_is_raised(
        self, close_db_session_tween, handler, pyramid_request
    ):
        handler.side_effect = RuntimeError("test_error")

        with pytest.raises(RuntimeError, match="^test_error$"):
            close_db_session_tween(pyramid_request)

        pyramid_request.db.close.assert_called_once_with()

    @pytest.fixture
    def close_db_session_tween(self, handler):
        return close_db_session_tween_factory(handler, mock.sentinel.registry)

    @pytest.fixture
    def handler(self):
        handler = mock.create_autospec(lambda request: None)  # pragma: nocover
        return handler

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.db = mock.MagicMock(spec_set=["close"])
        return pyramid_request
