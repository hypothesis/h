# -*- coding: utf-8 -*-
"""API view decorators for response headers"""

from h.views.api import API_VERSION_DEFAULT
from h.views.api.helpers.media_types import media_type_for_version, version_media_types


def version_media_type_header(subtype="json"):
    """View decorator to add response header indicating API version"""

    def deco(wrapped):
        def wrapper(context, request):
            response = wrapped(context, request)
            # Assume default version...
            version_media_type = media_type_for_version(API_VERSION_DEFAULT, subtype)
            # ...Unless we can determine otherwise from the Accept header
            if request.accept:
                version_accepts = [
                    t for t in request.accept if t in version_media_types()
                ]
                if any(version_accepts):
                    # If the Accept header contains any values that match a known version
                    # media type, that's the version that would have been matched
                    # and used
                    version_media_type = version_accepts[0]

            response.headers["Hypothesis-Media-Type"] = version_media_type
            return response

        return wrapper

    return deco
