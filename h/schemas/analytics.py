from typing import TypedDict

from h.schemas.base import JSONSchema


class EventSchema(JSONSchema):
    schema = {
        "type": "object",
        "required": ["event"],
        "properties": {
            "event": {
                "type": "string",
                "enum": ["client.realtime.apply_updates"],
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
