import json

from importlib_resources import files

from h.schemas import ValidationError
from h.schemas.base import JSONSchema
from h.security import Permission
from h.services import BulkAnnotationService
from h.services.bulk_annotation import BadDateFilter, BadFieldSpec
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
    query_filter, fields = data["filter"], data["fields"]

    try:
        annotation_rows = request.find_service(BulkAnnotationService).annotation_search(
            # Use the authority from the authenticated client to ensure the user
            # is limited to items they have permission to request
            authority=request.identity.auth_client.authority,
            fields=fields,
            **query_filter,
        )

    except BadFieldSpec as err:
        # Emulate the format of the normal ValidationError's from a schema
        raise ValidationError(f"fields: {err}") from err

    except BadDateFilter as err:
        # We happen to know this is the updated field, because there's no other
        # but, it could easily be something else in the future
        raise ValidationError(str(err)) from err

    present_row = _get_present_row(fields)
    return get_ndjson_response((present_row(row) for row in annotation_rows))


def _get_present_row(fields):
    # The schema enforces this, but we currently rely on it being hard coded
    # so some belt and braces is in order. For example, the exact order matters
    assert fields == ["author.username", "group.authority_provided_id"]

    def present_row(row):
        username, authority_provided_id = row

        return {
            "author": {"username": username},
            "group": {"authority_provided_id": authority_provided_id},
        }

    return present_row
