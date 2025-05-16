"""Exceptions raised by :mod:`h.services`."""

from pyramid.request import Request
from requests import Response, Timeout


class ServiceError(Exception):
    """Base class for all :mod:`h.services` exception classes."""


class ValidationError(ServiceError):
    """A validation problem with a database model."""


class ConflictError(ServiceError):
    """An integrity problem with a database operation."""


class ExternalRequestError(Exception):
    def __init__(
        self,
        message: str | None = None,
        request: Request | None = None,
        response: Response | None = None,
        validation_errors: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self._message = message
        self._request = request
        self._response = response
        self._validation_errors = validation_errors

    @property
    def request(self) -> Request | None:
        """Return the request object."""
        return self._request

    @property
    def response(self) -> Response | None:
        """Return the response object."""
        return self._response

    @property
    def validation_errors(self) -> dict[str, str] | None:
        """Return the validation errors."""
        return self._validation_errors

    @property
    def url(self) -> str | None:
        """Return the request's URL."""
        return getattr(self._request, "url", None)

    @property
    def method(self) -> str | None:
        """Return the HTTP request method."""
        return getattr(self._request, "method", None)

    @property
    def request_body(self) -> str | None:
        """Return the request body."""
        return getattr(self._request, "body", None)

    @property
    def status_code(self) -> int | None:
        """Return the response's status code."""
        return getattr(self._response, "status_code", None)

    @property
    def reason(self) -> str | None:
        """Return the response's HTTP reason string, e.g. 'Bad Request'."""
        return getattr(self._response, "reason", None)

    @property
    def response_body(self) -> str | None:
        """Return the response body."""
        return getattr(self._response, "text", None)

    @property
    def is_timeout(self) -> bool:
        """Return True if the error was caused by a timeout."""
        return isinstance(self.__cause__, Timeout)

    def __repr__(self) -> str:
        # Include the details of the request and response for debugging. This
        # appears in the logs and in tools like Sentry and Papertrail.
        request = (
            "Request("
            f"method={self.method!r}, "
            f"url={self.url!r}, "
            f"body={self.request_body!r}"
            ")"
        )

        response = (
            "Response("
            f"status_code={self.status_code!r}, "
            f"reason={self.reason!r}, "
            f"body={self.response_body!r}"
            ")"
        )

        # The name of this class or of a subclass if one inherits this method.
        class_name = self.__class__.__name__

        return (
            f"{class_name}("
            f"message={self._message!r}, "
            f"request={request}, "
            f"response={response}, "
            f"validation_errors={self._validation_errors!r})"
        )

    def __str__(self) -> str:
        return repr(self)
