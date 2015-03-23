# -*- coding: utf-8 -*-
"""A Python client for the Hypothesis API."""
from .api_client import Client, APIError, ConnectionError, Timeout

__all__ = ['Client', 'APIError', 'ConnectionError', 'Timeout']


def _get_api_client(api_url, timeout, request):
    api_url = api_url or request.resource_url(request.root, "api")
    return Client(api_url, timeout)


def _validate_timeout(settings):
    key = "h.api_timeout"
    timeout = settings.get(key)
    if timeout is None:
        return None
    else:
        try:
            return float(timeout)
        except ValueError as err:
            raise RuntimeError(
                "Value {value} for setting {key} is invalid: {error}".format(
                    value=timeout, key=key, error=err))


def includeme(config):
    """Add a request.get_api_client() to the request object."""
    settings = config.registry.settings

    api_url = settings.get("h.api_url", "")
    timeout = _validate_timeout(settings)

    def get_api_client(request):
        return _get_api_client(api_url, timeout, request)

    config.add_request_method(get_api_client, 'api_client', reify=True)
