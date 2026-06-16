from h.schemas.base import JSONSchema


class UpsertCheckpointAPISchema(JSONSchema):
    """Validate a Hide & Reveal checkpoint upsert request."""

    schema = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "authority_provided_id": {"type": "string", "minLength": 1},
            "document_url": {"type": "string", "minLength": 1},
            # The value is parsed/validated as ISO 8601 in the view.
            "reveal_date": {"type": ["string", "null"]},
        },
        "required": ["authority_provided_id", "document_url"],
    }
