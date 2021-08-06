import sys

from pyramid.view import view_config


# Test seam. Patching `sys.exc_info` directly causes problems with pytest.
def _exc_info():
    return sys.exc_info()


def handle_exception(request, exception):  # pylint: disable=unused-argument
    """
    Handle an uncaught exception for the passed request.

    :param request: The Pyramid request which caused the exception.
    :param exception: The exception passed as context to the exception-handling view.
    """
    request.response.status_int = 500


def json_view(**settings):
    """Get the configuration decorator with JSON defaults."""
    settings.setdefault("accept", "application/json")
    settings.setdefault("renderer", "json")
    return view_config(**settings)
