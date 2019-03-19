# -*- coding: utf-8 -*-
"""API view decorators for response headers"""

from __future__ import unicode_literals

from h.views.api import API_VERSION_DEFAULT
from h.views.api.helpers.media_types import media_type_for_version


def version_media_type_header(wrapped):
    """View decorator to add response header indicating API version"""

    def wrapper(context, request):
        response = wrapped(context, request)
        # TODO: expand with logic for multiple versions once the app knows
        # about multiple versions
        version_media_type = media_type_for_version(API_VERSION_DEFAULT)
        response.headers["Hypothesis-Media-Type"] = version_media_type
        return response

    return wrapper
