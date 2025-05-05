import pytest
import requests

from h.services import exceptions
from h.services.exceptions import ExternalRequestError
from tests.common import factories


class TestServiceError:
    def test_it_is_an_exception(self):
        exc = exceptions.ServiceError("a message")

        assert isinstance(exc, Exception)
        assert isinstance(exc, exceptions.ServiceError)

    def test_it_can_set_message(self):
        exc = exceptions.ServiceError("a message")

        assert "a message" in repr(exc)


class TestValidationError:
    def test_it_extends_ServiceError(self):
        exc = exceptions.ValidationError("some message")

        assert isinstance(exc, exceptions.ValidationError)
        assert isinstance(exc, exceptions.ServiceError)

    def test_it_can_set_message(self):
        exc = exceptions.ValidationError("a message")

        assert "a message" in repr(exc)


class TestConflictError:
    def test_it_extends_ServiceError(self):
        exc = exceptions.ConflictError("some message")

        assert isinstance(exc, exceptions.ConflictError)
        assert isinstance(exc, exceptions.ServiceError)

    def test_it_can_set_message(self):
        exc = exceptions.ConflictError("a message")

        assert "a message" in repr(exc)


class TestExternalRequestError:
    def test_it(self):
        response = factories.requests.Response(
            status_code=418, reason="I'm a teapot", raw="Body text"
        )

        err = ExternalRequestError(response=response)

        assert err.status_code == 418
        assert err.reason == "I'm a teapot"
        assert err.response_body == "Body text"

    def test_it_when_theres_no_response(self):
        err = ExternalRequestError()

        assert err.request is None
        assert err.response is None
        assert err.status_code is None
        assert err.reason is None
        assert err.response_body is None
        assert not err.is_timeout

    @pytest.mark.parametrize(
        "message,request_,response,validation_errors,cause,expected",
        [
            (
                None,
                None,
                None,
                None,
                None,
                "ExternalRequestError(message=None, request=Request(method=None, url=None, body=None), response=Response(status_code=None, reason=None, body=None), validation_errors=None)",
            ),
            (
                "Connecting to Hypothesis failed",
                requests.Request(
                    "GET", "https://example.com", data="request_body"
                ).prepare(),
                factories.requests.Response(
                    status_code=400,
                    reason="Bad Request",
                    raw="Name too long",
                ),
                {"foo": ["bar"]},
                KeyError("cause"),
                "ExternalRequestError(message='Connecting to Hypothesis failed', request=Request(method='GET', url='https://example.com/', body='request_body'), response=Response(status_code=400, reason='Bad Request', body='Name too long'), validation_errors={'foo': ['bar']})",
            ),
        ],
    )
    def test_str(self, message, request_, response, validation_errors, cause, expected):
        err = ExternalRequestError(
            message=message,
            request=request_,
            response=response,
            validation_errors=validation_errors,
        )
        err.__cause__ = cause

        assert str(err) == expected
