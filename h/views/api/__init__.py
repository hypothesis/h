API_VERSIONS = ["v1", "v2"]
"""All of the app's known API versions"""

API_VERSION_DEFAULT = "v1"
"""
The current API version.

API requests will match to views supporting this version unless the request
specifies a different version with a properly-formatted Accept header
"""

__all__ = ("API_VERSIONS", "API_VERSION_DEFAULT")


def includeme(config):  # pragma: nocover
    config.scan(__name__)
