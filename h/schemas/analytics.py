from typing import TypedDict

from h.schemas.base import JSONSchema


class EventSchema(JSONSchema):
    schema = {
        "type": "object",
        "required": ["event"],
        "properties": {
            "event": {
                "type": "string",
                "enum": ["APPLY_PENDING_UPDATES"],
            },
        },
    }


class Event(TypedDict):
    event: str


class CreateEventSchema:
    """Validate the POSTed data of a create event request."""

    def __init__(self):
        self._structure = EventSchema()

    def validate(self, data: dict) -> Event:
        return self._structure.validate(data)
