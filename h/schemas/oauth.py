from typing import ClassVar, TypedDict

from h.schemas.base import JSONSchema


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
    def __init__(self):
        self._schema = OAuthCallbackSchema()

    def validate(self, data: dict) -> OAuthCallback:
        return self._schema.validate(data)


class OAuthTokenSchema(JSONSchema):
    schema: ClassVar = {
        "type": "object",
        "required": ["access_token"],
        "properties": {
            "access_token": {"type": "string"},
            "refresh_token": {"type": "string"},
            "expires_in": {"type": "integer", "minimum": 1},
        },
    }


class OAuthToken(TypedDict):
    access_token: str
    refresh_token: str
    expires_in: int


class ReadOAuthTokenSchema:
    def __init__(self):
        self._schema = OAuthTokenSchema()

    def validate(self, data: dict) -> OAuthToken:
        return self._schema.validate(data)
