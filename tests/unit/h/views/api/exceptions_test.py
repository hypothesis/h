from h.views.api import exceptions


class TestOAuthTokenError:
    def test_it_sets_type_and_message(self):
        exc = exceptions.OAuthTokenError("boom", "mytype")

        assert exc.type == "mytype"
        assert str(exc) == "boom"

    def test_it_sets_default_response_code(self):
        exc = exceptions.OAuthTokenError("boom", "mytype")

        assert exc.status_code == 401


class TestPayloadError:
    def test_it_sets_default_message_and_status(self):
        exc = exceptions.PayloadError()

        assert exc.status_code == 400
        assert str(exc) == "Expected a valid JSON payload, but none was found!"
