# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from h.views.api import API_VERSIONS


def media_type_for_version(version, subtype="json"):
    """
    Return the media type corresponding to a particular version string

    :arg version:  The major API version, e.g. ``"v1"``
    :type version: str
    :arg subtype:  The "subtype" of the content type desired; defaults
                   to ``"json"``
    :type subtype: str or None
    :rtype: str
    """
    return "application/vnd.hypothesis.{}+{}".format(version, subtype)


def valid_media_types(versions=None):
    """
    Return a list of all valid API media types

    This represents a list of all of the Accept header values that are known to
    the API. This includes all version-specific media types.

    An HTTP request to the API must contain either:

    * An empty Accept header
    * An Accept header containing at least one of the media types returned by
      this function.

    :arg versions: List of version strings to include in the valid media types.
                   Defaults to the app's known version list.
    :type versions: list(str) or None
    :rtype: list(str)
    """
    versions = versions or API_VERSIONS
    valid_types = ["*/*", "application/json"]
    for version in versions:
        valid_types.append(media_type_for_version(version))
    return valid_types
