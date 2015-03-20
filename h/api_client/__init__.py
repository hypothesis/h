# -*- coding: utf-8 -*-
"""A Python client for the Hypothesis API."""
from h.api_client.api_client import Client, APIError, ConnectionError, Timeout

__all__ = ['Client', 'APIError', 'ConnectionError', 'Timeout']


def includeme(config):
    config.include('.subscribers')
