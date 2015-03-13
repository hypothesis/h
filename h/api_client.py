# -*- coding: utf-8 -*-
"""A Python client for the Hypothesis API.

Provides simple functions for calling the Hypothes API over HTTP from Python.
These functions handle getting the correct configured API root URL for this
app, timeouts and API request failures, etc.

"""
import requests


def get(base_url, path, params):
    """Make an HTTP GET request to the Hypothesis API and return the response.

    :returns: the JSON response from the API as a Python object
    :rtype: dict or list

    :param base_url: The base URL to the Hypothesis API instance to use.
        For example: ``"http://hypothesis.is/api"``.

    :param path: The API path to request, for example: ``"/search"``.

    :param params: The params to pass in the URL's query string, for example:
        ``{"limit": 10}``.
    :type params: dict

    """
    url = "/".join([base_url.rstrip("/"), path.lstrip("/")])
    # TODO: Handle timeouts.
    return requests.get(url, params=params).json()
