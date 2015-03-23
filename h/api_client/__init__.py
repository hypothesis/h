# -*- coding: utf-8 -*-
"""A Python client for the Hypothesis API."""
from .api_client import Client, APIError, ConnectionError, Timeout

__all__ = ['Client', 'APIError', 'ConnectionError', 'Timeout']


def _validate_api_client_timeout(settings):
    key = "h.api_timeout"
    if key in settings:
        timeout = settings[key]
        try:
            timeout = float(timeout)
        except ValueError as err:
            raise RuntimeError("{key} setting is invalid: {value}".format(
                key=key, value=timeout))
        settings["h.api_timeout"] = timeout


def includeme(config):
    _validate_api_client_timeout(config.registry.settings)
    config.include('.subscribers')
