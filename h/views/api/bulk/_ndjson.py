import json
from itertools import chain
from typing import Iterable, Optional

from pyramid.response import Response


def get_ndjson_response(results: Optional[Iterable]) -> Response:
    """
    Create a streaming response for an NDJSON based end-point.

    :param results: Iterable series of responses to convert to JSON
    """
    if results is None:
        return Response(status=204)

    # When we get an iterator we must force the first return value to be
    # created to be sure input validation has occurred. Otherwise, we might
    # raise errors outside the view when called.
    results = iter(results)

    try:
        results = chain([next(results)], results)
    except StopIteration:
        results = []  # pylint: disable=redefined-variable-type

    # An NDJSON response is required
    return Response(
        app_iter=((json.dumps(result) + "\n").encode("utf-8") for result in results),
        status=200,
        content_type="application/x-ndjson",
    )
