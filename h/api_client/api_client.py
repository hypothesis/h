# -*- coding: utf-8 -*-
"""A Python client for the Hypothesis API."""
import requests
import pyramid.traversal


class APIError(Exception):

    """Raised when a request to the API fails for any reason."""

    pass


class ConnectionError(APIError):

    """Raised when a request to the API fails because of a network problem."""

    pass


class Timeout(APIError):

    """Raised when a request to the API times out."""

    pass


class HypothesisAPIClient(object):
    """A client for the Hypothesis API.

    Provides simple methods for calling the API over HTTP.

    Note that this class is deliberately decoupled from the Hypothesis Pyramid
    app and from Pyramid.

    """
    def __init__(self, base_url):
        """Initialize a new API client.

        :param base_url: The base URL to the Hypothesis API instance to use.
            For example: ``"http://hypothesis.is/api"``.

        """
        self.base_url = base_url

    def get(self, path, params=None):
        """Make a GET request to the Hypothesis API and return the response.

        :returns: the JSON response from the API as a Python object
        :rtype: dict or list

        :param path: The API path to request, for example: ``"/search"``.

        :param params: The params to pass in the URL's query string,
            for example: ``{"limit": 10}``.
        :type params: dict

        """
        url = "/".join([self.base_url.rstrip("/"), path.lstrip("/")])
        try:
            return requests.get(url, params=params, timeout=0.2).json()
        except requests.exceptions.ConnectionError as err:
            raise ConnectionError(err)
        except requests.exceptions.Timeout as err:
            raise Timeout(err)
        except requests.exceptions.RequestException as err:
            raise APIError(err)
