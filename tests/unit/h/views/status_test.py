from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPInternalServerError

from h.views.status import status


@pytest.mark.usefixtures("db")
class TestStatus:
    def test_it_returns_okay_on_success(self, pyramid_request, capture_message):
        result = status(pyramid_request)
        assert result
        capture_message.assert_not_called()

    def test_it_fails_when_database_unreachable(self, pyramid_request, db):
        db.execute.side_effect = Exception("explode!")

        with pytest.raises(HTTPInternalServerError) as exc:
            status(pyramid_request)

        assert "Database connection failed" in str(exc.value)

    def test_it_sends_test_messages_to_sentry(self, pyramid_request, capture_message):
        pyramid_request.params["sentry"] = ""

        status(pyramid_request)

        capture_message.assert_called_once_with("Test message from h's status view")

    @pytest.fixture
    def db(self, pyramid_request):
        db = mock.Mock()
        pyramid_request.db = db
        return db


@pytest.fixture(autouse=True)
def capture_message(patch):
    return patch("h.views.status.capture_message")
