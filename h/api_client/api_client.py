# -*- coding: utf-8 -*-
import urlparse

import requests


class APIError(Exception):

    """Raised when a request to the API fails for any reason."""

    pass


class ConnectionError(APIError):

    """Raised when a request to the API fails because of a network problem."""

    pass


class Timeout(APIError):

    """Raised when a request to the API times out."""

    pass


class Client(object):

    """A client for the Hypothesis API.

    Provides simple methods for calling the API over HTTP.

    Note that this class is deliberately decoupled from the Hypothesis Pyramid
    app and from Pyramid.

    """

    def __init__(self, base_url, timeout=None):
        """Initialize a new API client.

        :param base_url: The base URL to the Hypothesis API instance to use.
            For example: ``"http://hypothesis.is/api"``.

        :param timeout: How long to wait (in seconds) for a response from the
            API, before raising Timeout
        :type timeout: float

        """
        if not base_url.endswith("/"):
            base_url = base_url + "/"
        self.base_url = base_url

        self.timeout = timeout or 0.2

    def get(self, path, params=None):
        """Make a GET request to the Hypothesis API and return the response.

        :returns: the JSON response from the API as a Python object
        :rtype: dict or list

        :param path: The API path to request, for example: ``"/search"``.

        :param params: The params to pass in the URL's query string,
            for example: ``{"limit": 10}``.
        :type params: dict

        """
        url = urlparse.urljoin(self.base_url, path.lstrip("/"))
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
        except requests.exceptions.ConnectionError as err:
            raise ConnectionError(err)
        except requests.exceptions.Timeout as err:
            raise Timeout(err)
        except requests.exceptions.RequestException as err:
            raise APIError(err)

        try:
            return response.json()
        except ValueError as err:
            raise APIError(err)
