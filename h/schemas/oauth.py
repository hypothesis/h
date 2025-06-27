import logging
import secrets
from typing import Any, ClassVar, TypedDict

from pyramid.request import Request

from h.schemas.base import JSONSchema, ValidationError

logger = logging.getLogger(__name__)


class OAuthCallbackSchema(JSONSchema):
    schema: ClassVar = {  # type: ignore[misc]
        "type": "object",
        "required": ["code", "state"],
        "properties": {
            "code": {"type": "string"},
            "state": {"type": "string"},
        },
    }


class OAuthCallbackData(TypedDict):
    code: str
    state: str


class InvalidOAuthStateError(ValidationError):
    def __init__(self):
        super().__init__("Invalid OAuth state")


class RetrieveOAuthCallbackSchema:
    SESSION_KEY = "oauth2_state"

    def __init__(self, request: Request) -> None:
        self._schema = OAuthCallbackSchema()
        self._request = request

    def validate(self, data: dict[str, Any]) -> OAuthCallbackData:
        validated_data = self._schema.validate(data)

        if validated_data["state"] != self._request.session.pop(self.SESSION_KEY, None):
            raise InvalidOAuthStateError

        # Return only known keys from the data to make sure that code can't
        # make use of any unknown keys. The OAuth 2 spec requires that clients
        # ignore any unrecognised authorization response parameters.
        return {"code": validated_data["code"], "state": validated_data["state"]}

    def state_param(self) -> str:
        state = secrets.token_hex()
        self._request.session[self.SESSION_KEY] = state
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
