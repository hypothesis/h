"""
Validation schemas used in our implementation of OAuth 2.0.

https://datatracker.ietf.org/doc/html/rfc6749
"""

import logging
import secrets
from typing import Any, ClassVar, TypedDict

from pyramid.request import Request

from h.schemas.base import JSONSchema, ValidationError

logger = logging.getLogger(__name__)


class InvalidOAuth2StateParamError(ValidationError):
    """An invalid OAuth 2 state param was received."""

    def __init__(self):
        super().__init__("Invalid OAuth state")


class OAuth2RedirectSchema:
    """Schema for validating OAuth 2 authorization redirect requests."""

    def __init__(self, request: Request, session_key: str) -> None:
        self._request = request
        self.state_session_key = f"{session_key}.state"

    class OAuth2RedirectData(TypedDict):
        """Return type for OAuth2RedirectSchema.validate()."""

        code: str
        state: str

    def validate(self, data: dict[str, Any]) -> OAuth2RedirectData:
        """Validate `data` and return the validated copy.

        This includes validating the `state` param against a copy that was
        previously stored in the Pyramid session. Any existing state param in
        the Pyramid session will be deleted.
        """

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

        if validated_data["state"] != self._request.session.pop(
            self.state_session_key, None
        ):
            raise InvalidOAuth2StateParamError

        # Return only known keys from the data to make sure that code can't
        # make use of any unknown keys. The OAuth 2 spec requires that clients
        # ignore any unrecognised authorization response parameters.
        return {"code": validated_data["code"], "state": validated_data["state"]}

    def state_param(self) -> str:
        """Generate and return a new OAuth 2 state param.

        A copy of the newly-generated state param will also be stored in the
        Pyramid session. Any existing state param in the Pyramid session will
        be overwritten.
        """
        state = secrets.token_hex()
        self._request.session[self.state_session_key] = state
        return state
