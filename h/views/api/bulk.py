from itertools import chain

from pyramid.response import Response

from h.h_api.bulk_api import BulkAPI
from h.services.bulk_executor._executor import  AuthorityCheckingExecutor
from h.views.api.config import api_config


class FakeBulkAPI(BulkAPI):
    """Temporary stub for return values.

    When this work is complete, BulkAPI will return values for us. But right
    now it doesn't and we need something to prove we can build a return value.
    """

    return_content = True

    @classmethod
    def from_byte_stream(cls, byte_stream, executor, observer=None):
        super().from_byte_stream(byte_stream, executor, observer=None)

        if cls.return_content:
            yield b'["Line 1"]\n'
            yield b'["Line 2"]\n'
        else:
            return None


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk",
    request_method="POST",
    link_name="bulk",
    description="Perform multiple operations in one call",
    subtype="x-ndjson",
    permission="bulk_action",
)
def bulk(request):
    """
    Perform a bulk request which can modify multiple records in on go.

    This end-point can:

     * Upsert users
     * Upsert groups
     * Add users to groups

    This end-point is intended to be called using the classes provided by
    `h.h_api.bulk_api`.
    """

    results = FakeBulkAPI.from_byte_stream(
        request.body_file, executor=AuthorityCheckingExecutor()
    )

    # No return view is required
    if results is None:
        return Response(status=204)

    # An NDJSON response is required
    if results:
        # When we get an iterator we must force the first return value to be
        # created to be sure input validation has occurred. Otherwise we might
        # raise errors outside of the view
        results = chain([next(results)], results)

        return Response(
            app_iter=results, status=200, content_type="application/x-ndjson"
        )
