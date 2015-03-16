# -*- coding: utf-8 -*-
"""A Python client for the Hypothesis API."""
import requests
import pyramid.traversal


class APIError(Exception):

    """Exception that's raised when a request to the API fails."""

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

    def get(self, path, params):
        """Make a GET request to the Hypothesis API and return the response.

        :returns: the JSON response from the API as a Python object
        :rtype: dict or list

        :param path: The API path to request, for example: ``"/search"``.

        :param params: The params to pass in the URL's query string,
            for example: ``{"limit": 10}``.
        :type params: dict

        """
        url = "/".join([self.base_url.rstrip("/"), path.lstrip("/")])
        # TODO: Handle timeouts.
        try:
            return requests.get(url, params=params).json()
        except requests.exceptions.ConnectionError as err:
            raise APIError(err)
