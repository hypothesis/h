import logging
import secrets
from typing import ClassVar, TypedDict

from pyramid.request import Request

from h.schemas.base import JSONSchema, ValidationError

logger = logging.getLogger(__name__)


class OAuthCallbackSchema(JSONSchema):
    schema: ClassVar = {
        "type": "object",
        "required": ["code"],
        "properties": {
            "code": {"type": "string"},
            "state": {"type": "string"},
            "error": {"type": "string"},
            "error_description": {"type": "string"},
        },
    }


class OAuthCallback(TypedDict):
    code: str
    state: str | None
    error: str | None
    error_description: str | None


class ReadOAuthCallbackSchema:
    def __init__(self, request: Request) -> None:
        self._schema = OAuthCallbackSchema()
        self._request = request

    def validate(self, data: dict) -> OAuthCallback:
        if data.get("state") != self._request.session.pop("oauth2_state", None):
            raise ValidationError("Invalid oauth state")  # noqa: EM101, TRY003

        return self._schema.validate(data)

    def state_param(self) -> str:
        state = secrets.token_hex()
        self._request.session["oauth2_state"] = state
        return state


class OAuthTokenSchema(JSONSchema):
    schema: ClassVar = {
        "type": "object",
        "required": ["access_token", "refresh_token", "expires_in"],
        "properties": {
            "access_token": {"type": "string"},
            "refresh_token": {"type": "string"},
            "expires_in": {"type": "integer", "minimum": 1},
            "id_token": {"type": "string"},
        },
    }


class OAuthToken(TypedDict):
    access_token: str
    refresh_token: str
    expires_in: int
    id_token: str


class ReadOAuthTokenSchema:
    def __init__(self):
        self._schema = OAuthTokenSchema()

    def validate(self, data: dict) -> OAuthToken:
        return self._schema.validate(data)
