import logging
from typing import Any, ClassVar, TypedDict

from h.schemas.base import JSONSchema

logger = logging.getLogger(__name__)


class OpenIDTokenSchema(JSONSchema):
    schema: ClassVar = {  # type: ignore[misc]
        "type": "object",
        "required": ["id_token"],
        "properties": {
            "access_token": {"type": "string"},
            "refresh_token": {"type": "string"},
            "expires_in": {"type": "integer", "minimum": 1},
            "id_token": {"type": "string"},
        },
    }


class OpenIDTokenData(TypedDict):
    access_token: str | None
    refresh_token: str | None
    expires_in: int | None
    id_token: str


class RetrieveOpenIDTokenSchema:
    def __init__(self) -> None:
        self._schema = OpenIDTokenSchema()

    def validate(self, data: dict[str, Any]) -> OpenIDTokenData:
        return self._schema.validate(data)
