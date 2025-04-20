from pyramid.request import Request  # noqa: A005
from requests import RequestException, Response, Session


class ExternalRequestError(Exception):
    def __init__(self, request: Request, response: Response) -> None:
        self._request = request
        self._response = response

    @property
    def request(self) -> Request:
        return self._request

    @property
    def response(self) -> Response:
        return self._response


class HTTPService:
    """Send HTTP requests with `requests` and receive the responses."""

    def __init__(self) -> None:
        # A session is used so that cookies are persisted across
        # requests and urllib3 connection pooling is used (which means that
        # underlying TCP connections are re-used when making multiple requests
        # to the same host, e.g. pagination).

        # See https://docs.python-requests.org/en/latest/user/advanced/#session-objects
        self._session = Session()

    def request(self, method: str, url: str, timeout=(10, 10), **kwargs) -> Response:
        """
        Send a request with `requests` and return the response object.

        This method accepts the same arguments as `requests.Session.request`
        with the same meaning which can be seen here:

        https://requests.readthedocs.io/en/latest/api/#requests.Session.request

        :raises ExternalRequestError: For any request based failure or if the
            response is an error (4xx or 5xx response).
        """
        try:
            response = self._session.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
        except RequestException as err:
            raise ExternalRequestError(request=err.request, response=response) from err

    def get(self, *args, **kwargs) -> Response:
        return self.request("GET", *args, **kwargs)

    def put(self, *args, **kwargs) -> Response:
        return self.request("PUT", *args, **kwargs)

    def post(self, *args, **kwargs) -> Response:
        return self.request("POST", *args, **kwargs)

    def patch(self, *args, **kwargs) -> Response:
        return self.request("PATCH", *args, **kwargs)

    def delete(self, *args, **kwargs) -> Response:
        return self.request("DELETE", *args, **kwargs)


def factory(_context, _request) -> HTTPService:
    return HTTPService()
