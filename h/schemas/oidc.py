"""Validation schemas used in our implementation of OpenID Connect (OIDC)."""

from typing import Any, ClassVar, TypedDict

from h.schemas.base import JSONSchema


class OIDCTokenResponseSchema:
    """Schema for validating OIDC token responses."""

    class OIDCTokenResponseData(TypedDict):
        """Return type for OIDCTokenResponseSchema.validate()."""

        access_token: str | None
        refresh_token: str | None
        expires_in: int | None
        id_token: str

    def validate(self, data: dict[str, Any]) -> OIDCTokenResponseData:
        """Validate `data` and return the validated copy."""

        class Schema(JSONSchema):
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

        return Schema().validate(data)
