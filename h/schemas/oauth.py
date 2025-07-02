"""
Validation schemas used in our implementation of OAuth 2.0.

https://datatracker.ietf.org/doc/html/rfc6749
"""

import logging
from typing import Any, ClassVar, TypedDict

from h.schemas.base import JSONSchema, ValidationError

logger = logging.getLogger(__name__)


class InvalidOAuth2StateParamError(ValidationError):
    """An invalid OAuth 2 state param was received."""

    def __init__(self):
        super().__init__("Invalid OAuth state")


class OAuth2RedirectSchema:
    """Schema for validating OAuth 2 authorization redirect requests."""

    class OAuth2RedirectData(TypedDict):
        """Return type for OAuth2RedirectSchema.validate()."""

        code: str
        state: str

    @staticmethod
    def validate(data: dict[str, Any], expected_state) -> OAuth2RedirectData:
        """Validate `data` and return the validated copy."""

        class Schema(JSONSchema):
            schema: ClassVar = {  # type: ignore[misc]
                "type": "object",
                "required": ["code", "state"],
                "properties": {
                    "code": {"type": "string"},
                    "state": {"type": "string"},
                },
            }

        validated_data = Schema().validate(data)

        if validated_data["state"] != expected_state:
            raise InvalidOAuth2StateParamError

        # Return only known keys from the data to make sure that code can't
        # make use of any unknown keys. The OAuth 2 spec requires that clients
        # ignore any unrecognised authorization response parameters.
        return {"code": validated_data["code"], "state": validated_data["state"]}
