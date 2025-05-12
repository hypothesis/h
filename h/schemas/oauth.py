import logging
import secrets
from typing import Any, ClassVar, TypedDict

from pyramid.request import Request

from h.schemas.base import JSONSchema, ValidationError

logger = logging.getLogger(__name__)


class OAuthCallbackSchema(JSONSchema):
    schema: ClassVar = {  # type: ignore[misc]
        "type": "object",
        "required": ["code"],
        "properties": {
            "code": {"type": "string"},
            "state": {"type": "string"},
            "error": {"type": "string"},
            "error_description": {"type": "string"},
        },
    }


class OAuthCallbackData(TypedDict):
    code: str
    state: str | None
    error: str | None
    error_description: str | None


class RetrieveOAuthCallbackSchema:
    def __init__(self, request: Request) -> None:
        self._schema = OAuthCallbackSchema()
        self._request = request

    def validate(self, data: dict[str, Any]) -> OAuthCallbackData:
        state = data.get("state")
        if not state or state != self._request.session.pop("oauth2_state", None):
            msg = "Invalid oauth state"
            raise ValidationError(msg)

        return self._schema.validate(data)

    def state_param(self) -> str:
        state = secrets.token_hex()
        self._request.session["oauth2_state"] = state
        return state


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
