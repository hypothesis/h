import json

from importlib_resources import files

from h.schemas import ValidationError
from h.schemas.base import JSONSchema
from h.security import Permission
from h.services import BulkAnnotationService
from h.services.bulk_api import BadDateFilter, BulkAnnotation
from h.views.api.bulk._ndjson import get_ndjson_response
from h.views.api.config import api_config


class BulkAnnotationSchema(JSONSchema):
    _SCHEMA_FILE = files("h.views.api.bulk") / "annotation_schema.json"

    schema_version = 7
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.annotation",
    request_method="POST",
    link_name="bulk.annotation",
    description="Retrieve a large number of annotations in one go",
    subtype="x-ndjson",
    permission=Permission.API.BULK_ACTION,
)
def bulk_annotation(request):
    """Retrieve a large number of annotations at once for LMS."""

    # Once this has been applied, we know everything else is safe to use
    # without checking any further
    data = BulkAnnotationSchema().validate(request.json)
    query_filter = data["filter"]

    try:
        annotations = request.find_service(BulkAnnotationService).annotation_search(
            # Use the authority from the authenticated client to ensure the user
            # is limited to items they have permission to request
            authority=request.identity.auth_client.authority,
            username=query_filter["username"],
            created=query_filter["created"],
            limit=query_filter["limit"],
        )

    except BadDateFilter as err:
        # We happen to know this is the created field, because there's no other
        # but, it could easily be something else in the future
        raise ValidationError(str(err)) from err

    return get_ndjson_response(
        (_present_annotation(annotation) for annotation in annotations)
    )


def _present_annotation(annotation: BulkAnnotation) -> dict:
    return {
        "author": {"username": annotation.username},
        "group": {"authority_provided_id": annotation.authority_provided_id},
        "metadata": annotation.metadata,
    }
