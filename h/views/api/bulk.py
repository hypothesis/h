import json
from itertools import chain

from h_api.bulk_api import BulkAPI
from pyramid.response import Response

from h.security import Permission
from h.services.bulk_executor import BulkExecutor
from h.views.api.config import api_config


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk",
    request_method="POST",
    link_name="bulk",
    description="Perform multiple operations in one call",
    subtype="x-ndjson",
    permission=Permission.API.BULK_ACTION,
)
def bulk(request):
    """
    Perform a bulk request which can modify multiple records in on go.

    This end-point can:

     * Upsert users
     * Upsert groups
     * Add users to groups

    This end-point is intended to be called using the classes provided by
    `h_api.bulk_api`.
    """

    results = BulkAPI.from_byte_stream(
        request.body_file,
        executor=BulkExecutor(
            db=request.db, authority=request.identity.auth_client.authority
        ),
    )

    if results is None:
        return Response(status=204)

    # When we get an iterator we must force the first return value to be
    # created to be sure input validation has occurred. Otherwise we might
    # raise errors outside of the view when called

    try:
        results = chain(  # pylint: disable=redefined-variable-type
            [next(results)], results
        )
    except StopIteration:
        results = []

    # An NDJSON response is required
    return Response(
        app_iter=((json.dumps(result) + "\n").encode("utf-8") for result in results),
        status=200,
        content_type="application/x-ndjson",
    )
