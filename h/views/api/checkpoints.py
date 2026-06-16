from datetime import UTC, datetime

from pyramid.httpexceptions import HTTPNotFound

from h.schemas import ValidationError
from h.schemas.api.checkpoint import UpsertCheckpointAPISchema
from h.security import Permission
from h.services.checkpoint import CheckpointService, GroupNotFoundError
from h.views.api.config import api_config
from h.views.api.helpers.json_payload import json_payload


@api_config(
    versions=["v1", "v2"],
    route_name="api.checkpoints",
    request_method="POST",
    link_name="checkpoint.upsert",
    description="Create or update a Hide & Reveal checkpoint",
    permission=Permission.API.CHECKPOINT_UPSERT,
)
def upsert(request):
    """
    Create or update the Hide & Reveal checkpoint for a (group, document).

    Authorised clients (currently only the LMS) push the reveal_date for a
    group + document on each launch. The write is an upsert keyed on
    (group, document): the most recent write wins.
    """
    appstruct = UpsertCheckpointAPISchema().validate(json_payload(request))

    reveal_date = _parse_reveal_date(appstruct.get("reveal_date"))

    checkpoint_service = request.find_service(CheckpointService)
    try:
        checkpoint = checkpoint_service.upsert(
            authority=request.identity.auth_client.authority,
            authority_provided_id=appstruct["authority_provided_id"],
            document_url=appstruct["document_url"],
            reveal_date=reveal_date,
        )
    except GroupNotFoundError as err:
        raise HTTPNotFound(str(err)) from err

    return {
        "id": checkpoint.id,
        "reveal_date": (
            checkpoint.reveal_date.isoformat() if checkpoint.reveal_date else None
        ),
    }


def _parse_reveal_date(raw: str | None) -> datetime | None:
    """Parse an ISO 8601 reveal_date into a naive UTC datetime, matching the model."""
    if not raw:
        return None

    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as err:
        raise ValidationError(  # noqa: TRY003
            f"reveal_date is not a valid ISO 8601 datetime: {raw!r}"  # noqa: EM102
        ) from err

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)

    return parsed
