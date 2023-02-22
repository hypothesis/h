from h_api.bulk_api import BulkAPI

from h.security import Permission
from h.services.bulk_executor import BulkExecutor
from h.views.api.bulk._ndjson import get_ndjson_response
from h.views.api.config import api_config


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.action",
    request_method="POST",
    link_name="bulk.action",
    description="Perform multiple operations in one call",
    subtype="x-ndjson",
    permission=Permission.API.BULK_ACTION,
)
def bulk_action(request):
    """
    Perform a bulk request which can modify multiple records in on go.

    This end-point can:

     * Upsert users
     * Upsert groups
     * Add users to groups

    This end-point is intended to be called using the classes provided by
    `h_api.bulk_api`.
    """

    return get_ndjson_response(
        BulkAPI.from_byte_stream(
            request.body_file,
            executor=BulkExecutor(
                db=request.db, authority=request.identity.auth_client.authority
            ),
        )
    )
