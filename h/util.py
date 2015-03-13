# -*- coding: utf-8 -*-
"""Shared utility functions for the app."""

def api_url(request):
    """Return the URL to the Hypothesis API for this app.

    Always return the URL _without_ a trailing /.

    """
    return request.registry.settings.get(
        "h.api_url", request.resource_url(request.root, "api")).rstrip("/")
