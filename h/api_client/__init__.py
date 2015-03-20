# -*- coding: utf-8 -*-
"""A Python client for the Hypothesis API."""
from .api_client import Client, APIError, ConnectionError, Timeout

__all__ = ['Client', 'APIError', 'ConnectionError', 'Timeout']


def includeme(config):
    config.include('.subscribers')
